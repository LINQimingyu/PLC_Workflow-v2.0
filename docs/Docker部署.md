# Docker 部署

Docker 方式运行 Linux 容器中的 Web 工作台、34 个专家目录、41 个 Skill、项目规划 Agent、资料检索、FDC/TT 和厂内任务包。项目数据保存在 Docker 命名卷，默认只发布宿主机 `127.0.0.1:8772`。Windows 原有启动方式继续可用。

## 安装并启动

需要 Docker Engine + Docker Compose v2；Windows 使用 Docker Desktop 的 Linux containers 模式。宿主机不需要另装 Python 或 Node.js。首次构建需要访问 Docker Hub、PyPI 和 npm；日常离线任务不下载模型。

```sh
git clone https://github.com/LINQimingyu/PLC_Workflow-v2.0.git
cd PLC_Workflow-v2.0
docker compose up --build --detach --wait
```

公开仓库可直接克隆；推送代码或访问受限功能时需完成 GitHub 登录。构建在 Node 阶段编译并测试前端，再将静态文件复制进 Python 3.13 镜像；运行进程使用 UID/GID `10001:10001`。Windows 专用依赖不进入 Linux 依赖锁。

首次运行是空工作空间，不自动导入本机历史案例、备份或登录凭证。启动成功后，在自己的终端读取私有登录链接并粘贴到浏览器：

```sh
docker compose exec -T workbench cat /data/.local/login-url.txt
```

必须使用链接中的 `http://127.0.0.1:8772` 地址；`localhost` 与其他域名不会通过 Host/Origin 检查。链接包含登录凭证，不要分享。每次重启会生成新链接，旧会话失效。常规日志不输出登录链接。

## 更换端口

将根目录 `.env.example` 复制为 `.env`，修改：

```dotenv
PLC_WORKFLOW_PORT=8872
```

重新运行 `docker compose up --detach --wait`，再读取新的登录链接。容器内部仍使用 8772；浏览器 Origin、健康检查及宿主机映射使用所配置的新端口。`.env` 不提交到 Git。

## 项目规划 Agent 的 API Key

默认挂载空文件，手动建项目、专家任务包、离线检索和确定性工具均可使用。需要“AI 协助创建”时：

1. 在宿主机 `deploy/secrets/planner-api-key.txt` 写入自己的 API Key，使用 UTF-8 单行文本；该目录已被 Git 和 Docker 构建上下文排除。
2. 在根目录 `.env` 配置文件路径和密钥对应的接口地址：

   ```dotenv
   PLC_WORKFLOW_PLANNER_KEY_PATH=./deploy/secrets/planner-api-key.txt
   PLC_WORKFLOW_PLANNER_KEY_BASE_URL=https://api.deepseek.com
   ```

3. Linux 宿主机需要让容器 UID 10001 可读取该文件。例如创建后执行 `sudo chown 10001:10001 deploy/secrets/planner-api-key.txt` 和 `sudo chmod 400 deploy/secrets/planner-api-key.txt`；Docker Desktop 按宿主机文件共享权限处理。密钥文件的父目录也必须允许容器访问。
4. 执行 `docker compose up --detach --force-recreate --wait`，在工作台中保存模型和接口设置。Docker 模式中密钥输入和清除按钮禁用，密钥通过只读挂载提供。兼容接口需要在界面设置同一个 API 地址；换地址后不会复用原接口密钥。

密钥不写入镜像、环境变量值、项目数据库、任务包或日志。更换或移除密钥需更新宿主机文件/`.env` 并重新创建容器。未挂载可读取的文件或地址不匹配时，界面显示尚未配置。此密钥仅供新建项目的规划 Agent；原生工程模型配置依赖 Windows 凭据管理器，仍使用 Windows 版。外部模型只接收 public 描述，厂内接口仍须由用户明确确认部署位置。

## 数据、停机与更新

工程、业务 SQLite、上传资料、任务状态和设置统一位于命名卷 `/data`，卷在同一 Compose 项目下重建容器时继续使用。不要同时启动多个副本操作同一卷。

```sh
docker compose ps
docker compose logs --tail 100 workbench
docker compose stop
```

先停止服务再备份，可避免 SQLite 与附件在复制时发生变化：

```sh
docker compose stop
docker compose cp workbench:/data ./backup-before-update
docker compose start
```

备份包含私有资料和登录文件，保存在自己的受控位置。`docker compose down` 保留命名卷；不要使用 `down --volumes`，该参数会删除数据卷。改变仓库目录名、Compose 项目名或 Docker 主机会使用其他卷，迁移前先备份。

更新源码与镜像：

```sh
git pull --ff-only
docker compose up --build --detach --wait
```

容器重新启动后需读取新的登录链接。Windows 版的既有 workspace 不自动迁入 Docker，迁移前应单独备份和验证数据。

## 远程服务器

在服务器上部署后，通过 SSH 转发同一个端口，再在本机浏览器打开服务器生成的登录链接：

```sh
ssh -N -L 8772:127.0.0.1:8772 user@server
```

如更换端口，两侧转发端口应与 `.env` 一致。当前提供本机单用户访问方式，应用继续严格校验 Host、Origin、操作员会话和 CSRF。

## 平台能力与验证

- Linux 容器运行项目、资料、流程、专家任务包与离线工具；GX Works2 桌面程序、真实编译、GX Simulator、Windows 硬件网关和在线 PLC 操作仍需单独的 Windows 环境，不因容器健康状态正常而被记为通过。
- ST 语法扩展未在本镜像中构建，对应能力继续返回不可用；不将缺失依赖当作验证成功。
- 仓库中的 `Docker deployment` GitHub Actions 会在 Linux 构建镜像，运行前后端检查，并核对静态界面、非默认映射端口、登录、Host/Origin、CSRF、项目资料和容器重启持久化。
- `deploy/smoke.py` 专用于 CI 的全新工作空间，会创建合成项目并重启容器，不要对日常工作卷运行。

Docker 机制参考：[多阶段构建](https://docs.docker.com/build/building/multi-stage/)、[Compose 入门](https://docs.docker.com/compose/gettingstarted/)、[命名卷](https://docs.docker.com/engine/storage/volumes/)。
