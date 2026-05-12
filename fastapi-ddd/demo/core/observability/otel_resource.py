# coding: utf-8
"""构建带进程级身份的 OpenTelemetry Resource。

默认的 ``Resource.create({"service.name": ...})`` 只会合并 SDK 与 ``otel`` 探测器
（环境变量等），**不会**自动生成 ``service.instance.id``，也不会启用 ``process`` 探测器，
因此多 Uvicorn worker 时各进程 Resource 可能过于相似。此处为每进程补充实例 ID 与 pid。
"""

from __future__ import annotations

import os
import socket

from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


def _primary_local_ipv4() -> str:
    """选取本机用于出站路由的 IPv4，避免仅靠 hostname 解析成 127.0.0.1。"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
            # 不实际通信；用于让内核选出默认源地址（RFC 5737 TEST-NET-1）
            s.connect(("192.0.2.1", 1))
            return s.getsockname()[0]
    except OSError:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def build_service_resource(*, service_name: str) -> Resource:
    """返回含 ``service.name``、以本机 IP 为主的 ``service.instance.id`` 与 ``process.pid``。

    ``service.instance.id`` 使用 ``{ip}:{pid}``，同机多 Uvicorn worker 仍互不重复。
    """
    ip = _primary_local_ipv4()
    instance_id = f"{ip}"
    return Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_INSTANCE_ID: instance_id,
            ResourceAttributes.PROCESS_PID: os.getpid(),
        }
    )
