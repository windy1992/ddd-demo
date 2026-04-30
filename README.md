##  FastAPI DDD Toolkit

一个基于 FastAPI + Domain-Driven Design (DDD) 的后端开发脚手架，帮助构建高内聚、低耦合、可扩展的业务系统。

### 项目简介

本项目旨在提供一套清晰的 DDD 分层结构，结合 FastAPI 的高性能特性，用于构建复杂业务系统（如推荐系统、A/B 测试平台等）。

核心目标：

- 明确业务边界（Bounded Context）
- 解耦业务逻辑与框架
- 支持复杂领域建模
- 提供统一的工程实践规范


已有功能:
- 配置文件、数据库基本设置
- 仓储类抽象及实现、rabbitmq发布订阅
- 用户注册、登录、授权
- 事件存储 outbox实现


### TODO
- 长时处理过程及事件处理优化
- tick、trace