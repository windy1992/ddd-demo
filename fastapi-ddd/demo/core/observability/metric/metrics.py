# coding: utf-8
"""OpenTelemetry MeterProvider 与 OTLP/HTTP 指标导出。"""

from __future__ import annotations

import logging
from typing import Optional

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader

from demo.core.observability.otel_resource import build_service_resource

logger = logging.getLogger(__name__)

_metrics_started: bool = False


def _otlp_metrics_url(base: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/v1/metrics"):
        return b
    return f"{b}/v1/metrics"


def setup_metrics(
    *,
    enabled: bool,
    service_name: str,
    otlp_endpoint: str = "http://127.0.0.1:4318",
    export_interval_seconds: int = 60,
    metric_reader: Optional[MetricReader] = None,
) -> None:
    """配置全局 MeterProvider。测试可传入 metric_reader（如 InMemoryMetricReader）。"""
    global _metrics_started
    if _metrics_started:
        logger.debug("metrics 已初始化，跳过重复 setup")
        return
    if not enabled:
        return

    resource = build_service_resource(service_name=service_name)
    if metric_reader is not None:
        reader: MetricReader = metric_reader
    else:
        interval_ms = max(1, export_interval_seconds) * 1000
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=_otlp_metrics_url(otlp_endpoint)),
            export_interval_millis=interval_ms,
        )
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    _metrics_started = True
    logger.info("OpenTelemetry metrics 已启用，service=%s", service_name)


def shutdown_metrics() -> None:
    """关闭 MeterProvider。"""
    global _metrics_started
    if not _metrics_started:
        return
    provider = metrics.get_meter_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()  # type: ignore[no-untyped-call]
    _metrics_started = False
    logger.debug("OpenTelemetry metrics 已关闭")


def get_meter(name: str, version: str = "") -> Meter:
    """获取业务用 Meter（需在 setup_metrics 之后调用）。"""
    return metrics.get_meter(name, version)
