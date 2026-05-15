# FastAPI DDD Toolkit

基于 **FastAPI** 与 **领域驱动设计（DDD）** 的全栈脚手架，后端采用分层架构保持业务与框架解耦，前端提供开箱即用的管理后台。

## 仓库结构

| 路径 | 说明 |
|------|------|
| `fastapi-ddd/demo/` | Python 后端包 `demo`，含应用入口、领域模块与测试 |
| `fastapi-ddd/admin-web/` | React 管理前端（Vite + Tailwind + shadcn/ui） |

---

## 后端（`fastapi-ddd/demo`）

### 设计目标

- **限界上下文**：按业务边界组织模块（当前示例为 `iam`）。
- **分层**：领域 / 应用 / 基础设施 / API 分离，降低对框架的耦合。
- **统一基础设施**：配置、数据库、消息、可观测性等集中初始化。

### 已有能力

- **配置**：YAML（`config-{APP_ENV}.yaml`），默认 `APP_ENV=dev`，加载 `config-dev.yaml`。
- **数据库**：SQLAlchemy 2.x + asyncmy，异步连接池；`deleted_at BIGINT`（毫秒时间戳）软删除，`0` 表示未删除。
- **IAM**：用户注册/登录、JWT、RBAC（角色 / 权限）；路由前缀 `/auth`；支持分页查询。
- **仓储**：通用仓储抽象与实现（`core/repository`），含 `unique_constraint()` 组合唯一约束工具。
- **消息**：RabbitMQ 发布/订阅相关封装（`core/rabbitmq`）；`UserDeleted` / `RoleDeleted` 事件示例。
- **领域事件与 Outbox**：`DomainEventPublisher` / `DefaultDomainEventSubscriber` 与事务内事件落库配合（`core/event_store`）。
- **可观测性**：OpenTelemetry（FastAPI 自动埋点、OTLP/HTTP 导出），通过配置 `telemetry` 开关与端点。
- **异常处理**：全局 `RequestValidationError` → 400、业务 `ValueErrorException` → 400、其余 → 500，统一 JSON 格式。

### 环境要求

- Python **≥ 3.12**
- **MySQL**（与 `config-dev.yaml` 中 `db` 一致）
- 可选：**RabbitMQ**（跑消息相关测试时）
- 可选：支持 OTLP/HTTP 的采集端（如本地 `4318`），用于链路/指标导出

### 快速开始

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

### 数据库迁移

首次建表：

```bash
uv run pytest demo/tests/test_table_create.py -s -v
```

`is_deleted` → `deleted_at` 字段迁移（已有库执行一次）：

```bash
uv run pytest demo/tests/test_migrate_deleted_at.py -s -v
```

### 可观测性

在对应环境的 YAML 中设置：

```yaml
telemetry:
  enabled: true
  otlp_endpoint: http://127.0.0.1:4318
  export_interval_seconds: 60
```

### 主要 API（IAM）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/auth/login` | 表单登录，返回 Token |
| `POST` | `/auth/user` | 注册用户（用户名/密码不可为空） |
| `GET` | `/auth/users?page=1&page_size=10` | 用户分页列表（需 admin） |
| `DELETE` | `/auth/users/{user_id}` | 删除用户（需 admin） |
| `POST` | `/auth/users/{user_id}/roles` | 分配角色（需 admin） |
| `DELETE` | `/auth/users/{user_id}/roles` | 移除角色（需 admin） |
| `POST` | `/auth/role` | 新建角色（需 admin） |
| `GET` | `/auth/roles?page=1&page_size=10` | 角色分页列表（需 admin） |
| `DELETE` | `/auth/roles/{role_id}` | 删除角色（需 admin） |
| `POST` | `/auth/roles/{role_id}/permissions` | 分配权限（需 admin） |
| `DELETE` | `/auth/roles/{role_id}/permissions` | 移除权限（需 admin） |
| `POST` | `/auth/permission` | 新建权限（需 admin） |
| `GET` | `/auth/permissions?page=1&page_size=10` | 权限分页列表（需 admin） |
| `DELETE` | `/auth/permissions/{permission_id}` | 删除权限（需 admin） |

交互式文档：启动后访问 `/docs`（Swagger UI）。

### 测试

```bash
cd fastapi-ddd/demo
uv run pytest
```

部分用例依赖 MySQL/RabbitMQ 等外部服务，未就绪时可能跳过或失败。

### 模块一览（`demo` 包）

- `core/config` — 配置加载与全局访问
- `core/db` — 异步 MySQL 会话
- `core/repository` — 仓储基类、`create_table`、`unique_constraint`
- `core/rabbitmq` — 消息生产/消费
- `core/event_store` — 领域事件与订阅（含 Outbox 事务配合）
- `core/observability` — OTel 初始化与 FastAPI 插桩
- `core/error` — 统一异常与 HTTP 映射
- `iam/` — 身份与访问管理：domain / application / infrastructure / api

---

## 前端（`fastapi-ddd/admin-web`）

React 18 + TypeScript 管理后台，基于 Vite 构建。

### 技术栈

| 库 | 用途 |
|----|------|
| React 19 + React Router 7 | 页面路由 |
| Tailwind CSS 4 | 样式 |
| shadcn/ui（Radix UI） | 组件库 |
| Sonner | Toast 通知 |
| Vite 5 | 构建工具 |

### 快速开始

```bash
cd fastapi-ddd/admin-web
npm install
npm run dev
```

默认访问 `http://localhost:5173`，需后端服务已启动（CORS 已允许该地址）。

### 页面功能

| 页面 | 功能 |
|------|------|
| 用户管理 | 分页列表、注册用户、分配/移除角色、删除用户 |
| 角色管理 | 分页列表、新建角色、分配/移除权限、删除角色 |
| 权限管理 | 分页列表、新建权限、删除权限 |

所有列表均支持 **每页条数切换**（10 / 20 / 50 / 100），分配弹窗中已分配项禁止取消勾选。

---

版本信息见 `fastapi-ddd/demo/pyproject.toml` 中的 `version`。
