"""Build public, source-only usage packs for Doubao/Codex using the standard library.

Never imports the application or opens its workspaces, cases, credentials or logs.
Real execution batches must be exported through the workbench's classification gate.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {"doubao": "豆包", "codex": "Codex"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def read_source(path):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError("源码路径不能指向项目目录之外")
    return path.read_bytes()


def build_pack(platform):
    label = PLATFORMS[platform]
    files = {}
    for path in sorted((ROOT / "AI使用包/共用").glob("*")):
        if path.suffix in {".md", ".txt"}:
            files["AI使用包/共用/" + path.name] = read_source(path)
    for path in sorted((ROOT / "AI使用包" / label).glob("*")):
        if path.suffix in {".md", ".txt"}:
            files["AI使用包/" + label + "/" + path.name] = read_source(path)
    for name in ["Docker部署.md", f"{label}安装使用.md"]:
        files["docs/" + name] = read_source(ROOT / "docs" / name)
    for name in ["LICENSE", "LICENSE-SCOPE.md", "NOTICE", "THIRD_PARTY_NOTICES.md", "UPSTREAM.json"]:
        files["来源许可/" + name] = read_source(ROOT / "app" / name)

    agents, skills, packs = [], [], []
    for path in sorted((ROOT / "app/agents").rglob("agent.json")):
        agents.append(json.loads(read_source(path)))
    for path in sorted((ROOT / "app/skills").rglob("skill.json")):
        metadata = json.loads(read_source(path))
        skills.append(metadata)
        # Use the shipped path rather than an unchecked catalog-provided filename.
        relative = path.parent.relative_to(ROOT / "app/skills").as_posix()
        files["方法库/" + relative + ".txt"] = (
            encode(metadata) + b"\n\n" + read_source(path.with_name("SKILL.md"))
        )
    for path in sorted((ROOT / "app/process-packs").rglob("pack.json")):
        packs.append(json.loads(read_source(path)))
    ids = {value["id"] for value in skills}
    if not agents or not skills or not packs or any(not set(agent["skills"]) <= ids for agent in agents):
        raise ValueError("源码目录缺失或专家引用了不存在的方法")
    files["目录/专家与方法目录.json"] = encode({"agents": agents, "skills": skills})
    files["目录/候选工艺包.json"] = encode(packs)
    files["目录/前置规划Agent.json"] = read_source(ROOT / "app/creation-agent.json")
    if platform == "codex":
        files["AI使用包/Codex/项目规则-AGENTS.md"] = read_source(ROOT / "AGENTS.md")

    files["00_从这里开始.txt"] = (
        f"PLC Workflow v2.0 · {label}使用包\n\n"
        f"先读取 AI使用包/{label}/ 中的开始使用材料，再读取 AI使用包/共用/项目说明.md。\n"
        "本包只包含项目源码自带的说明、目录、方法与许可，不包含可运行的完整源码或真实业务任务。\n"
        "角色和方法不自动安装到聊天客户端；只按当前问题选择材料。\n"
        "若客户端不能读取 ZIP，先在自己的电脑解压，再按需粘贴 TXT/JSON/Markdown 文本。\n"
        "真实任务的 task.json、return-template.json 和来源必须另从工作台按 external/public 规则导出。\n"
        "完整源码：https://github.com/LINQimingyu/PLC_Workflow-v2.0 （公开源码，Apache-2.0）\n"
    ).encode("utf-8")
    manifest = {
        "format_version": 1, "platform": platform, "classification": "public",
        "content_type": "shipped-source-usage-only", "contains_business_workspace": False,
        "counts": {"agents": len(agents), "skills": len(skills), "process_packs": len(packs)},
        "files": [{"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                  for name, data in sorted(files.items())],
    }
    files["manifest.json"] = encode(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    return buffer.getvalue(), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=[*PLATFORMS, "all"], default="all")
    parser.add_argument("--output", type=Path, default=ROOT / ".qa/ai-usage")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for platform in PLATFORMS if args.platform == "all" else [args.platform]:
        raw, manifest = build_pack(platform)
        target = args.output / f"PLC_Workflow-v2.0-{PLATFORMS[platform]}使用包.zip"
        target.write_bytes(raw)
        print(json.dumps({"output": str(target.resolve()), "bytes": len(raw), **manifest["counts"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
