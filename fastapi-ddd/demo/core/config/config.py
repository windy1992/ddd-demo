# coding: utf-8

from typing import Optional

from pydantic import BaseModel, Field


class DBConfig(BaseModel):
    driver: str
    host: str
    port: int
    user: str
    password: str
    database: str

    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    echo: bool = False

    def build_dsn(self) -> str:
        return (
            f"{self.driver}://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )


class TokenConfig(BaseModel):
    secret_key: str = "secret"
    algorithm: str = "HS256"
    expire_hours: int = 24


class LogConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    name: str
    debug: bool


class TelemetryConfig(BaseModel):
    """OpenTelemetry：OTLP/HTTP 导出，默认关闭。"""

    enabled: bool = False
    otlp_endpoint: str = "http://127.0.0.1:4318"
    export_interval_seconds: int = 60
    service_name: Optional[str] = None


class RoleDeletedMessageConfig(BaseModel):
    """RoleDeleted 出队/订阅使用的 RabbitMQ 与事件类型。"""
    amqp_url: str = "amqp://admin:admin1@127.0.0.1/"
    queue_name: str = "iam.role_deleted"
    fanout_exchange: str = "iam.role_deleted.fanout"
    event_type: str = "RoleDeleted"


class UserDeletedMessageConfig(BaseModel):
    """UserDeleted 出队/订阅使用的 RabbitMQ 与事件类型。"""
    amqp_url: str = "amqp://admin:admin1@127.0.0.1/"
    queue_name: str = "iam.user_deleted"
    fanout_exchange: str = "iam.user_deleted.fanout"
    event_type: str = "UserDeleted"

class MessagesConfig(BaseModel):
    role_deleted_message: RoleDeletedMessageConfig = Field(
        default_factory=RoleDeletedMessageConfig
    )
    user_deleted_message: UserDeletedMessageConfig = Field(
        default_factory=UserDeletedMessageConfig
    )


class TaskletsConfig(BaseModel):
    """常驻后台进程配置。enabled 填写各 tasklet 的 Python 模块路径，
    每个模块须暴露 async def main() 入口。"""

    enabled: list[str] = []
    restart_delay_seconds: int = 5


class Config(BaseModel):
    app: AppConfig
    db: DBConfig
    token: TokenConfig = Field(default_factory=TokenConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    messages: MessagesConfig = Field(default_factory=MessagesConfig)
    tasklets: TaskletsConfig = Field(default_factory=TaskletsConfig)