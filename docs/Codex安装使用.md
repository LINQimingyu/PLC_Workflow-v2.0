# 给 Codex 安装和使用本项目

建议用 Codex 本地项目打开仓库根目录，负责环境检查、安装启动、源码维护及明确的专家任务分析。根目录 `AGENTS.md` 是项目规则入口；34 个专家与 41 个 Skill 仍按实际项目路由按需读取，不安装到用户全局目录。

## 本地桌面项目

1. 使用有仓库权限的 GitHub 账号克隆 `https://github.com/LINQimingyu/PLC_Workflow-v2.0.git`。已有副本先检查本地修改，再按需要更新。
2. 在 Codex 桌面端添加本地项目文件夹，选仓库根目录，而不是只选择 `app/`。应能看到 `AGENTS.md`、`README.md`、安装脚本和 Compose 配置。
3. 新建该本地项目下的 Codex 对话，复制 [安装启动提示词](../AI使用包/Codex/安装启动提示词.md)。提示词文件不会自动执行，需由用户在对话中发起任务。
4. Windows 直接运行需要 Python 3.13 和 Node.js 22.14 或更高版本。Codex 可按现有脚本安装、构建、启动，并核对 `http://127.0.0.1:8772/api/health`。无需额外模型 Key 才能安装；“AI 协助创建”的模型配置是之后的独立选择。

在自己的 PowerShell 中手动安装启动也可以：

```powershell
Set-Location '你的仓库目录'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\安装与构建.ps1'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\启动工作台.ps1'
```

Docker 用户直接复制 [Docker 部署](Docker部署.md) 的启动命令。让 Codex 检查容器状态和持久卷；不要将正常运行的 Windows workspace 未经迁移直接覆盖进容器卷。

## Codex CLI

已经安装并登录官方 Codex CLI 的用户，可在仓库根目录启动 `codex`，再发送同一安装提示词。账号登录由用户本人完成，项目不携带或复制 Codex 凭据。

只读了解源码时可运行：

```sh
codex exec --sandbox read-only "读取 AGENTS.md 和 README.md，说明项目结构、安装方式与尚未验证的能力；不要读取 workspace 或任何凭据，不修改文件。"
```

这条命令会发起 Codex 模型任务，使用你自己的账号额度；本次交付没有代你执行它。需要交接说明包时运行 `python deploy/export_ai_usage.py --platform codex`，输出 `.qa/ai-usage/PLC_Workflow-v2.0-Codex使用包.zip`；该包不替代完整源码仓库。

## 日常业务和源码维护

- 业务任务：在工作台按依赖建立批次；普通云端模型只使用经过 public 检查的外部任务包。让 Codex 根据 `task.json`、绑定 Skill、来源及 `return-template.json` 分析。将 JSON 回传导入工作台，由工程师审查。
- 代码维护：在本地项目中描述具体要修改的行为。让 Codex 保留原件、避免提交 workspace/凭据，运行对应检查，并区分源码测试和现场能力。
- 本地客户端不代表模型位于厂内。普通 Codex 服务接收的资料仍按外部目的地处理；不要读取或发送内部业务资料。目录中已有项目资料不等于任务已经授权读取。

## Codex 云端环境

有云端功能的账号可自行将私有仓库接入并创建环境。云端用于代码阅读、开发与 Linux 检查，长期工作台部署仍选本机或自有服务器；云端 Linux 环境不会自动具备 GX Works2 桌面软件、硬件网关和现场连接。

网络可用且 Python 3.13、Node.js 满足版本要求时，可在环境设置阶段执行：

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r app/requirements/factory-linux-py313.lock.txt
cd app/web
npm ci --no-audit --no-fund
npm run build
cd ../..
```

之后的检查为 `.venv/bin/python -m pytest app/evals -q` 和在 `app/web/` 运行 `npm test`。环境实际提供的运行时和网络由使用者核对；不要假定云端有 Docker 守护进程。仓库现有 `Docker deployment` CI 已提供独立 Linux 镜像及启动检查。

## 当前交付的验证边界

说明包生成及格式检查、项目现有测试可以本地验证。未替用户创建 Codex 云端环境、改变账号连接或运行付费 Codex 任务；实际安装由对应环境中的真实执行结果确认。

官方依据：[Windows 本地项目与运行环境](https://learn.chatgpt.com/docs/app/windows)、[项目与对话](https://learn.chatgpt.com/docs/projects?surface=app)、[非交互 CLI](https://learn.chatgpt.com/docs/non-interactive-mode)、[云端环境](https://learn.chatgpt.com/docs/environments/cloud-environments)。
