# FastAPI DDD Toolkit

基于 **FastAPI** 与 **领域驱动设计（DDD）** 的后端脚手架，用于搭建边界清晰、业务与框架解耦、便于扩展的服务（例如推荐、实验平台等复杂领域）。

## 仓库结构

| 路径 | 说明 |
|------|------|
| `fastapi-ddd/demo/` | 可运行的 Python 包 `demo`，含应用入口、领域模块与测试 |

根目录 README 描述整体项目；包内依赖与脚本见 `fastapi-ddd/demo/pyproject.toml`。

## 设计目标

- **限界上下文**：按业务边界组织模块（当前示例为 `iam`）。
- **分层**：领域 / 应用 / 基础设施 / API 分离，降低对框架的耦合。
- **统一基础设施**：配置、数据库、消息、可观测性等集中初始化。

## 已有能力

- **配置**：YAML（`config-{APP_ENV}.yaml`），默认 `APP_ENV=dev`，加载 `config-dev.yaml`。
- **数据库**：SQLAlchemy 2.x + asyncmy，异步连接池；启动时 `init_env()` 中完成 `set_up`。
- **IAM**：用户注册与登录、JWT、基于角色的访问控制示例；路由前缀 `/auth`。
- **仓储**：通用仓储抽象与实现（`core/repository`）。
- **消息**：RabbitMQ 发布/订阅相关封装（`core/rabbitmq`）。
- **领域事件与 Outbox**：`DomainEventPublisher` / `DefaultDomainEventSubscriber` 等与事务内事件落库配合的示例（`core/event_store`）。
- **可观测性**：OpenTelemetry（FastAPI 自动埋点、OTLP/HTTP 导出），通过配置 `telemetry` 开关与端点。

## 环境要求

- Python **≥ 3.12**
- **MySQL**（与 `config-dev.yaml` 中 `db` 一致；测试可能依赖真实库）
- 可选：**RabbitMQ**（跑消息相关测试时）
- 可选：支持 OTLP/HTTP 的采集端（如本地 `4318`），用于链路/指标导出

## 快速开始

在包目录安装依赖并启动（建议使用 [uv](https://github.com/astral-sh/uv)）：

```bash
cd fastapi-ddd/demo
uv sync
export APP_ENV=dev   # 可选，默认即为 dev
uv run python -m demo.main
```

服务默认监听 `0.0.0.0:8000`。也可：

```bash
uv run uvicorn demo.main:app --host 0.0.0.0 --port 8000 --reload
```

根据环境复制并修改 `config-dev.yaml`（或新增 `config-<环境>.yaml`），至少核对 **数据库连接** 与 **`token.secret_key`** 等敏感项。

### 可观测性

在对应环境的 YAML 中设置，例如：

```yaml
telemetry:
  enabled: true
  otlp_endpoint: http://127.0.0.1:4318
  export_interval_seconds: 60
  # service_name: optional-override
```

## 主要 API 示例（IAM）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/auth/login` | 表单登录，返回 Token |
| `POST` | `/auth/user` | 注册用户 |
| `GET` | `/auth/users` | 用户列表（需 admin） |
| `POST` | `/auth/role` | 新建角色（需 admin） |
| … | `/auth/...` | 其余权限相关接口见 `iam/api/auth.py` |

交互式文档：启动后访问 `/docs`（Swagger UI）。

## 测试

```bash
cd fastapi-ddd/demo
uv run pytest
```

部分用例依赖 MySQL/RabbitMQ 等外部服务，未就绪时可能跳过或失败，需按 `tests/` 与本地配置对齐环境。

## 模块一览（`demo` 包）

- `core/config` — 配置加载与全局访问  
- `core/db` — 异步 MySQL 会话  
- `core/repository` — 仓储基类与实现  
- `core/rabbitmq` — 消息生产/消费  
- `core/event_store` — 领域事件与订阅（含与连接依赖注入的配合）  
- `core/observability` — OTel 初始化与 FastAPI 插桩  
- `core/error` — 统一异常与 HTTP 映射  
- `iam/` — 身份与访问管理：domain / application / infrastructure / api  


---

版本信息见 `fastapi-ddd/demo/pyproject.toml` 中的 `version`。
