"""Import read-only historical copies and a clearly labelled synthetic TT example."""
from pathlib import Path
import argparse
import csv
import io
import json
import sys
from datetime import datetime,timedelta,timezone

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP/"src"))
from cim.service import FactoryService
from cim.commands import invoke


def synthetic_tt():
    out=io.StringIO()
    fields=["event_id","timestamp","station","equipment_id","glass_id","product","recipe","event","state"]
    w=csv.DictWriter(out,fieldnames=fields)
    w.writeheader()
    origin=datetime(2026,11,2,8,tzinfo=timezone(timedelta(hours=8)))
    for i in range(120):
        for station,start,duration in [("S1",i*10,10),("S2",10+i*20,20),("S3",30+i*20,15)]:
            for event,t in [("start",start),("end",start+duration)]:
                w.writerow({"event_id":f"demo-{i}-{station}-{event}","timestamp":(origin+timedelta(seconds=t)).isoformat(),
                            "station":station,"equipment_id":station+"-M1","glass_id":f"SYNTHETIC-{i:04}","product":"DEMO_ONLY",
                            "recipe":"SYNTHETIC_R1","event":event,"state":"processing"})
    return out.getvalue().encode("utf-8-sig")


def seed(service,case_root):
    existing={p["name"]:p for p in service.list_projects()}
    fdc_name="历史复盘 · 马达负载上报 FDC（待补验收依据）"
    if fdc_name not in existing:
        p=service.create_project(fdc_name,scenario="fdc",area="CF",cpu="Q26UDV",equipment="PHL08 / PHL10 Conveyor",classification="internal",
             requirements="历史业务目标：马达负载上报 FDC，用户已确认业务目标达成。当前复盘须核对点表、缩放、周期、断线行为、纳入/排除通道和工程验证。需求单原文件为空；PHL10 R11540/R11544/R11548 未改原因未知。当前未重新执行 GX 编译、扫描或现场测试。")
        paths=[("001input/PHL 8线/8#CV4_7_CONV_4.csv","source"),("001input/PHL 10线/7_CONV_4修改前.csv","source"),
               ("002output/PHL08线/8#CV4_7_CONV_4_改造后.csv","candidate"),("002output/PHL10线/7_CONV_4修改后.csv","candidate")]
        imported=[]
        for relative,kind in paths:
            path=case_root/relative
            if not path.is_file():
                raise FileNotFoundError("历史案例缺少文件: "+relative)
            d=service.add_document(p["id"],service.detail(p["id"])["project"]["revision"],path.name,path.read_bytes(),
                    classification="internal",kind=kind,metadata={"provenance":str(path),"historical":True,"field_validation_this_run":False})
            imported.append(d)
        revision=service.detail(p["id"])["project"]["revision"]
        for before,after in [(imported[0],imported[2]),(imported[1],imported[3])]:
            invoke(service,p["id"],"csv-compare",{"expected_revision":revision,"before_id":before["id"],"after_id":after["id"]})
        service.plan_tasks(p["id"],revision)
    tt_name="合成演示 · FA 产线 TT 改善（非现场数据）"
    if tt_name not in existing:
        p=service.create_project(tt_name,scenario="tt",area="FA",cpu="Q26UDV",equipment="Conveyor",classification="internal",
             requirements="仅演示日志质量、瓶颈候选与完成数校准。全部事件为合成数据，非现场证据。TT 指产线节拍及产能改善；当前模型不含故障/质量/换型/批处理/重入。演示成功不证明面板产线收益。")
        raw=synthetic_tt()
        d=service.add_document(p["id"],1,"SYNTHETIC_tt_events.csv",raw,classification="internal",metadata={"synthetic":True,"provenance":"scripts/seed_factory_workspace.py"})
        revision=service.detail(p["id"])["project"]["revision"]
        analysis=invoke(service,p["id"],"tt-analyze",{"expected_revision":revision,"source_id":d["id"],"terminal_station":"S3", "window_start":"2026-11-02T08:00:00+08:00","window_end":"2026-11-02T08:20:00+08:00","synthetic":True,"parallel":{"S1":1,"S2":1,"S3":1}})
        config={"stations":[{"id":"S1","process_seconds":10},{"id":"S2","process_seconds":20},{"id":"S3","process_seconds":15}],"buffers":[1,1],"duration_seconds":1200,"release_interval_seconds":10}
        invoke(service,p["id"],"simulate",{"expected_revision":revision,"source_ids":[d["id"]],"config":config,
             "scenario":{"stations":[{"id":"S1","process_seconds":10},{"id":"S2","process_seconds":15},{"id":"S3","process_seconds":15}]},
             "observed_completed":analysis["result"]["completed"],"tolerance":.1})
        service.plan_tasks(p["id"],revision)
    # Development seed reconciliation is allowed only before any attempt exists.
    # Never change a running/historical contract when the catalog is updated.
    with service.connect(True) as db:
        for p in service._list(db,"project"):
            if p["name"] not in {fdc_name,tt_name} or service._list(db,"attempt",p["id"]):
                continue
            refreshed=0
            for t in service._list(db,"task",p["id"]):
                snap=service.registry.snapshot(t["agent_id"])
                if t["status"]=="queued" and t["definition"]!=snap:
                    t["definition"]=snap
                    service._put(db,"task",t)
                    refreshed+=1
            if refreshed:
                service._audit(db,p["id"],"seed.catalog_refreshed_before_first_execution",{"tasks":refreshed})
    return service.list_projects()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--workspace",type=Path,default=APP.parent/"workspace"/"business")
    parser.add_argument("--cases",type=Path,default=APP.parents[1]/"项目案例"/"马达负载上报FDC开发")
    args=parser.parse_args()
    projects=seed(FactoryService(args.workspace),args.cases)
    print(json.dumps({"seeded":[{"id":p["id"],"name":p["name"]} for p in projects]},ensure_ascii=True))
