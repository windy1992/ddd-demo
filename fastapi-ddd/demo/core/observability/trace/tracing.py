# coding: utf-8
"""OpenTelemetry TracerProvider 与 OTLP/HTTP 导出封装。"""

from __future__ import annotations

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Tracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

from demo.core.observability.otel_resource import build_service_resource

logger = logging.getLogger(__name__)

_tracing_started: bool = False


def _otlp_traces_url(base: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/v1/traces"):
        return b
    return f"{b}/v1/traces"


def setup_tracing(
    *,
    enabled: bool,
    service_name: str,
    otlp_endpoint: str = "http://127.0.0.1:4318",
    span_exporter: Optional[SpanExporter] = None,
) -> None:
    """配置全局 TracerProvider。测试可传入 span_exporter 跳过 OTLP。"""
    global _tracing_started
    if _tracing_started:
        logger.debug("tracing 已初始化，跳过重复 setup")
        return
    if not enabled:
        return

    resource = build_service_resource(service_name=service_name)
    provider = TracerProvider(resource=resource)
    if span_exporter is not None:
        exporter: SpanExporter = span_exporter
    else:
        exporter = OTLPSpanExporter(endpoint=_otlp_traces_url(otlp_endpoint))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracing_started = True
    logger.info("OpenTelemetry tracing 已启用，service=%s", service_name)


def shutdown_tracing() -> None:
    """关闭 TracerProvider（刷新未导出 span）。"""
    global _tracing_started
    if not _tracing_started:
        return
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()  # type: ignore[no-untyped-call]
    _tracing_started = False
    logger.debug("OpenTelemetry tracing 已关闭")


def get_tracer(name: str, version: str = "") -> Tracer:
    """获取业务用 Tracer（需在 setup_tracing 之后调用）。"""
    return trace.get_tracer(name, version)
