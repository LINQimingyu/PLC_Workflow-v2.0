"""Local factory launcher: isolated settings, no telemetry or automatic cloud jobs."""
from __future__ import annotations
import argparse
import os
import secrets
import threading
import webbrowser
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=8772)
    parser.add_argument("--workspace",type=Path,default=Path(__file__).resolve().parents[3]/"workspace")
    parser.add_argument("--open-browser",action="store_true")
    args=parser.parse_args()
    if not 1024<=args.port<=65535:
        parser.error("端口范围 1024..65535")
    root=args.workspace.resolve()
    local=root/".local"
    local.mkdir(parents=True,exist_ok=True)
    from filelock import FileLock
    with FileLock(local/"factory-service.lock",timeout=0):
        run_server(args,root,local)


def run_server(args,root,local):
    os.environ["PLC_AI_DATA_DIR"]=str(local/"gxworks-settings")
    os.environ["HAYSTACK_TELEMETRY_ENABLED"]="false"
    os.environ["DO_NOT_TRACK"]="1"
    os.environ["HF_HUB_OFFLINE"]="1"
    os.environ["TRANSFORMERS_OFFLINE"]="1"
    from integrations.web.app import create_app
    from .workbench import FactoryWorkbench
    import uvicorn
    token=secrets.token_urlsafe(32)
    origin=f"http://127.0.0.1:{args.port}"
    service=FactoryWorkbench(root/"engineering",root/"engineering-state")
    # No upstream agent credential publication: native MCP remains a separate explicit configuration.
    app=create_app(root/"engineering",service=service,origin=origin,operator_token=token)
    url=origin+"/#cim?token="+token
    server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=args.port,workers=1,access_log=False))
    stopped=threading.Event()
    def open_ready():
        import time
        while not stopped.wait(.1):
            if server.started:
                (local/"login-url.txt").write_text(url,encoding="utf-8")
                (local/"server.pid").write_text(str(os.getpid()),encoding="ascii")
                if args.open_browser:
                    webbrowser.open(url)
                return
    threading.Thread(target=open_ready,daemon=True).start()
    try:
        server.run()
    finally:
        stopped.set()


if __name__=="__main__":
    main()
