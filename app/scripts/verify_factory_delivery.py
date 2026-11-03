"""Offline delivery audit: skill format, seed provenance and original bytes."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP/"src"))
from cim.service import FactoryService


def verify(workspace):
    service=FactoryService(workspace,read_only=True)
    original_files=[]
    examples=[]
    for project in service.list_projects():
        d=service.detail(project["id"])
        examples.append({"name":project["name"],"id":project["id"],"revision":project["revision"],
                         "tasks":len(d["tasks"]),"analyses":len(d["analyses"]),"attempts":len(d["attempts"])})
        for doc in d["documents"]:
            provenance=doc.get("metadata",{}).get("provenance")
            if doc.get("metadata",{}).get("historical"):
                current=hashlib.sha256(Path(provenance).read_bytes()).hexdigest()
                assert current==doc["sha256"],"原件与导入时的哈希不符"
                original_files.append({"name":doc["name"],"sha256":current,"unchanged":True})
    return {"upstream":json.loads((APP/"UPSTREAM.json").read_text(encoding="utf-8")),
            "agents":len(service.registry.agents),"skills":len(service.registry.skills),"process_packs":len(service.registry.packs),
            "examples":examples,"historical_originals":original_files,
            "st_frontend_dependency_available":importlib.util.find_spec("tree_sitter_iec61131_3_st") is not None,
            "native_compile_executed":False,"online_plc_write_executed":False,"field_acceptance":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--workspace",type=Path,default=APP.parent/"workspace/business")
    parser.add_argument("--output",type=Path,default=APP/".qa/delivery-audit.json")
    args=parser.parse_args()
    result=verify(args.workspace)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"agents":result["agents"],"skills":result["skills"],"originals_unchanged":len(result["historical_originals"])},ensure_ascii=True))
