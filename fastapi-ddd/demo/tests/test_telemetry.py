# coding: utf-8
"""可观测性组件测试。

OpenTelemetry 在单进程内不允许替换已设置的 TracerProvider / MeterProvider，
因此内存 exporter 相关断言合并到同一用例，避免多次 set provider。
"""

from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from fastapi.testclient import TestClient

from demo.core.observability import (
    get_meter,
    get_tracer,
    setup_metrics,
    setup_tracing,
    shutdown_metrics,
    shutdown_tracing,
)


def test_telemetry_disabled_setup_is_noop():
    setup_tracing(enabled=False, service_name="demo")
    setup_metrics(enabled=False, service_name="demo")
    shutdown_tracing()
    shutdown_metrics()


def test_memory_trace_and_metrics_single_setup():
    span_exporter = InMemorySpanExporter()
    metric_reader = InMemoryMetricReader()
    setup_tracing(
        enabled=True,
        service_name="test-svc",
        span_exporter=span_exporter,
    )
    setup_metrics(
        enabled=True,
        service_name="test-svc",
        metric_reader=metric_reader,
    )
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("op1"):
        pass
    meter = get_meter(__name__)
    counter = meter.create_counter("test_counter")
    counter.add(1, {"k": "v"})
    metrics_data = metric_reader.get_metrics_data()
    shutdown_tracing()
    shutdown_metrics()
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "op1"
    assert metrics_data is not None
    assert len(metrics_data.resource_metrics) >= 1


def test_app_lifespan_openspec():
    """telemetry 关闭时，带 lifespan 的 app 可正常启动。"""
    from demo.main import app

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
