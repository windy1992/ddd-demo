from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from demo.core.config.set_up import get_config
from demo.core.observability.trace.tracing import setup_tracing, shutdown_tracing
from demo.core.observability.metric.metrics import setup_metrics, shutdown_metrics

from demo.core.observability.trace.tracing import get_tracer
from demo.core.observability.metric.metrics import get_meter


def set_up(enabled: bool, service_name: str, otlp_endpoint: str, export_interval_seconds: int):
    setup_tracing(
        enabled=enabled,
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
    )
    setup_metrics(
        enabled=enabled,
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        export_interval_seconds=export_interval_seconds,
    )


def shut_down():
    shutdown_tracing()
    shutdown_metrics()

def instrument_app(app: FastAPI):
    cfg = get_config()
    tel = cfg.telemetry
    service_name = tel.service_name or cfg.app.name
    set_up(
        enabled=tel.enabled,
        service_name=service_name,
        otlp_endpoint=tel.otlp_endpoint,
        export_interval_seconds=tel.export_interval_seconds,
    )
    FastAPIInstrumentor.instrument_app(app)


def uninstrument_app(app: FastAPI):
    FastAPIInstrumentor.uninstrument_app(app)
    shut_down()

__all__ = ["set_up", "shut_down", "get_tracer", "get_meter", "instrument_app", "uninstrument_app"]