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


class Config(BaseModel):
    app: AppConfig
    db: DBConfig
    token: TokenConfig = Field(default_factory=TokenConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
