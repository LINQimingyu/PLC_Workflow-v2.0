"""CI-only smoke test: creates synthetic data in a fresh Compose workspace."""
import base64
import http.cookiejar
import json
import os
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


ORIGIN = "http://127.0.0.1:" + os.environ.get("PLC_WORKFLOW_PORT", "8772")
client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(path, body=None, headers=None, status=200):
    data = None if body is None else json.dumps(body).encode()
    req = Request(ORIGIN + path, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        response = client.open(req, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == status, (path, response.status, status)
        return response.read()


def login():
    raw = subprocess.run(["docker", "compose", "exec", "-T", "workbench", "cat", "/data/.local/login-url.txt"],
                         check=True, capture_output=True, text=True).stdout.strip()
    assert raw.startswith(ORIGIN + "/#cim?token=")
    token = parse_qs(urlsplit(raw).fragment.split("?", 1)[1])["token"][0]
    session = json.loads(request("/api/session", {"token": token}))
    return {"Origin": ORIGIN, "x-csrf-token": session["csrf"]}


def main():
    assert json.loads(request("/api/health"))["application"] == "gxworks-agent"
    assert b"<html" in request("/").lower()
    request("/api/cim/projects", status=401)
    request("/api/health", headers={"Host": "untrusted.invalid"}, status=403)
    request("/api/health", headers={"Origin": "https://untrusted.invalid"}, status=403)
    headers = login()
    catalog = json.loads(request("/api/cim/catalog"))
    assert len(catalog["agents"]) == 34 and len(catalog["skills"]) == 41
    settings = json.loads(request("/api/cim/planner/settings"))
    assert settings["key_read_only"] and not settings["has_key"]
    request("/api/cim/projects", {"name": "blocked without CSRF"}, status=403)
    project = json.loads(request("/api/cim/projects", {"name": "Docker synthetic smoke", "classification": "internal"}, headers, 201))
    route = f"/api/cim/projects/{project['id']}"
    request(route + "/commands/document", {"expected_revision": 1, "name": "synthetic.txt",
            "data_base64": base64.b64encode("容器持久化测试".encode()).decode(), "classification": "internal"}, headers)
    assert json.loads(request(route + "/search?q=" + "%E5%AE%B9%E5%99%A8"))["citations"]
    subprocess.run(["docker", "compose", "restart", "workbench"], check=True, stdout=subprocess.DEVNULL)
    for _ in range(120):
        try:
            if json.loads(request("/api/health"))["status"] == "ok":
                break
        except (OSError, AssertionError):
            pass
        time.sleep(.5)
    else:
        raise AssertionError("Container did not become ready after restart")
    request(route, status=401)
    login()
    detail = json.loads(request(route))
    assert detail["project"]["name"] == "Docker synthetic smoke" and len(detail["documents"]) == 1
    print("Docker smoke passed: static UI, mapped port, login, Host/Origin, CSRF, catalog, documents and restart persistence.")


if __name__ == "__main__":
    main()
