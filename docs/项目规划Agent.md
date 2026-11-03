# 项目规划 Agent 与工作流

左侧 **工作空间 → 工作流** 是工作台的完整操作说明；项目里的 **项目流程地图** 则展示该项目的真实状态与待办。

## 工艺能力包的用途

- **Agent**：谁分析，负责什么，交付什么。
- **Skill**：采用什么方法、步骤与判断边界。
- **工艺能力包**：同一工段的工序、约束、配方、来源、相关专家及案例上下文。
- **工作流**：如何组织前置依赖、回传、人工接受、验证与归档。

当前 ARRAY、CF、CELL、FA 四个包均为候选骨架，尚无已确认现场约束。绑定后会随专家和 Skill 进入任务定义快照，供执行时识别工艺前提及缺项；不能据此声明现场工艺已验证。项目创建不会修改全局目录或把项目 Skill 安装为全局 Skill。

## 使用 AI 协助创建

1. 在项目工作台点击 **AI 协助创建**，或在工作流页点击 **由项目规划 Agent 协助创建**。
2. 展开 **项目规划 Agent · 模型连接与 API Key**。默认 DeepSeek 官方 API，当前预设地址 `https://api.deepseek.com`，模型 `deepseek-flash`；也可以明确设置兼容接口和模型 ID。
3. Windows 直接运行时，在页面输入 API Key 并保存到 Windows 凭据管理器；Docker 部署时按 [Docker 部署](Docker部署.md) 挂载只读密钥文件，在页面只保存模型与接口设置。两种方式都按 API 地址隔离密钥，更换地址不会沿用另一个地址的 Key。配置保存本身不调用模型。
4. 输入可发送给模型的需求描述并选择描述分级。外部 API 只允许 public；厂内接口需由操作员明确确认地址及实际模型均为厂内批准部署。输入描述之外的既有项目和原始文件不会被创建请求读取。
5. 点击 **让 Agent 梳理需求**。未知工段、CPU 等保留待确认，模型提出问题。填写补充说明可继续澄清；每次明确提交补充会发起一轮模型请求。
6. 核对并修改项目名称、场景、工段、CPU、设备与需求；按需调整补充专家和工艺包。系统自动加入场景与 CPU 基础专家及程序、工艺、证据审查角色，Skill 由实际专家定义导出。
7. 查看自动生成的配置预览。手动修改字段或能力后，重新点击 **预览专家、Skill 与任务流程**。
8. 点击 **按配置创建项目与任务**。项目与任务在同一事务内创建，任务均为待执行；需求仍须你具名确认，后续任务由你逐步执行和审查。

规划 Agent 使用项目内 `requirements` 和 `impact-scope` 方法。它可以组合现有能力，不能创建任意工具权限、运行程序、代为审查或完成现场验证。

## 请求、版本与恢复

- 一轮请求使用稳定请求 ID。相同 ID 与相同内容重读或重放，不会再次调用模型；不同内容不能复用同一 ID。
- 网络状态不明时，先点击 **读取本次请求状态**。系统不自动重发模型调用。失败后明确点击规划或补充按钮，才会发起新请求。
- 无效 JSON、空响应、未完成输出或目录外的能力不会创建项目。
- 相同草案和相同配置重复创建，只返回已经创建的项目；不同配置会提示冲突。
- 创建后设备或 CPU 改变，原配置的适用签名失效；新任务采用基础路由并显示提示，不沿用错误 CPU 的专家。
- 草案及对话保存在本地业务数据库，项目保存创建草案 ID 和配置来源。描述分级在多轮对话中继承，不能把受限描述派生为更低分级项目。

## 本地接口

| 接口 | 作用 |
|---|---|
| `GET /api/cim/workflow-guide` | 七阶段详细用法、任务循环与能力包实际成熟度 |
| `GET /api/cim/planner/settings` | 模型配置及 Key 是否已保存；不返回 Key |
| `POST /api/cim/planner/settings` | 保存模型连接或 Key，受既有认证与 CSRF 保护 |
| `POST /api/cim/project-drafts` | 明确发起一轮规划；含 request_id、brief、input_classification，可带 parent_id |
| `GET /api/cim/project-drafts/{id}` | 读取已记录的规划请求状态与结果 |
| `POST /api/cim/project-setup/preview` | 校验 fields、agent_ids、pack_ids，生成配置及 fingerprint |
| `POST /api/cim/project-setup/create` | 以 draft_id、配置和 fingerprint 原子创建项目与待执行任务 |

## 验证边界

在 `app/` 下运行 `../.venv/Scripts/python.exe -m pytest evals -q`；在 `app/web/` 下运行 `npm test`、`npm run build`、`node tests/factory.e2e.mjs`、`node tests/workflow.e2e.mjs`、`node tests/planner.e2e.mjs`。

规划浏览器验收仅使用端口 18774、`.qa/planner-browser-workspace/`、内存假凭据和注入的合成模型，结果保存在 `.qa/planner-browser-results.json`。这些检查证明界面与接口流转，不代表已经用用户的真实 DeepSeek Key 完成付费调用，也不代表 PLC 编译、模拟或现场通过。

官方接口资料：[首次调用](https://api-docs.deepseek.com/)、[JSON 输出](https://api-docs.deepseek.com/guides/json_mode/)。模型 ID 可在界面修改，实际可用性以提供方与账号权限为准。
