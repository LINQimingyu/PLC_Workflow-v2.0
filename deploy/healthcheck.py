"""Check the container listener using the exact browser-facing Host header."""
import json
import os
from urllib.request import Request, urlopen


def main():
    port = int(os.environ.get("PLC_WORKFLOW_PORT", "8772"))
    request = Request("http://127.0.0.1:8772/api/health", headers={"Host": f"127.0.0.1:{port}"})
    with urlopen(request, timeout=3) as response:
        if json.load(response).get("application") != "gxworks-agent":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
