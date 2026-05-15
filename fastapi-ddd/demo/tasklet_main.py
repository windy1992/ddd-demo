# coding: utf-8
"""Tasklet Supervisor：以独立子进程启动各 tasklet，主进程负责保活。

运行方式：
    python -m demo.tasklet_main
    APP_ENV=prod python fastapi-ddd/demo/tasklet_main.py

约定：yaml tasklets.enabled 列出各 tasklet 的 Python 模块路径，每个模块须暴露 async def main()。
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import multiprocessing
import os
import signal
import sys
import time

from demo.core.config import get_config, set_up
from demo.init_env import init_env

logger = logging.getLogger(__name__)


def _child_entry(module_path: str) -> None:
    init_env()
    logging.basicConfig(level=get_config().log.level)
    asyncio.run(importlib.import_module(module_path).main())


class TaskletSupervisor:
    def __init__(self, module_paths: list[str], restart_delay: int) -> None:
        self._module_paths = module_paths
        self._restart_delay = restart_delay
        self._procs: dict[str, multiprocessing.Process] = {}
        self._running = True

    def _spawn(self, path: str) -> None:
        proc = multiprocessing.Process(
            target=_child_entry, args=(path,),
            name=path.rsplit(".", 1)[-1],
            daemon=True,  # 主进程正常退出时由 Python 自动清理
        )
        proc.start()
        self._procs[path] = proc
        logger.info("spawned %s  pid=%d", path, proc.pid)

    def _kill_all(self) -> None:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)  # 避免 killpg 误杀自身
        try:
            os.killpg(os.getpgrp(), signal.SIGTERM)
        except ProcessLookupError:
            pass
        for proc in self._procs.values():
            proc.join(timeout=5)
        try:
            os.killpg(os.getpgrp(), signal.SIGKILL)  # 超时兜底
        except ProcessLookupError:
            pass

    def _on_exit(self, signum: int, _frame: object) -> None:
        logger.info("signal %d received, shutting down", signum)
        self._running = False
        self._kill_all()
        sys.exit(0)

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._on_exit)
        signal.signal(signal.SIGINT, self._on_exit)

        for path in self._module_paths:
            self._spawn(path)

        while self._running:
            for path, proc in list(self._procs.items()):
                if not proc.is_alive():
                    exit_code = proc.exitcode
                    proc.join(timeout=0)
                    logger.warning(
                        "tasklet %s exited (code=%s), restart in %ds",
                        path, exit_code, self._restart_delay,
                    )
                    time.sleep(self._restart_delay)
                    if self._running:
                        self._spawn(path)
            time.sleep(1)


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    os.setpgrp()  # 成为进程组 leader，子进程继承同一 PGID
    set_up()
    cfg = get_config()
    logging.basicConfig(level=cfg.log.level)

    if not cfg.tasklets.enabled:
        logger.warning("no tasklets configured, exiting")
        sys.exit(0)

    logger.info(
        "starting supervisor with %d tasklet(s): %s",
        len(cfg.tasklets.enabled), cfg.tasklets.enabled,
    )
    TaskletSupervisor(cfg.tasklets.enabled, cfg.tasklets.restart_delay_seconds).run()
