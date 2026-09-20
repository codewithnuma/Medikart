# ============================================================
# latency.py
# ============================================================

import time
import logging
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class Timer:
    """
    Simple latency timer.

    Usage:

        with Timer("router"):
            result = router_model.invoke(prompt)
    """

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed = time.perf_counter() - self.start_time

        logger.info(
            "[LATENCY] %s = %.3f seconds",
            self.name,
            self.elapsed,
        )

        print(
            f"[LATENCY] {self.name}: "
            f"{self.elapsed:.3f}s"
        )


@contextmanager
def timer(name: str):
    """
    Functional version of Timer.
    """

    start = time.perf_counter()

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start

        logger.info(
            "[LATENCY] %s = %.3f seconds",
            name,
            elapsed,
        )

        print(
            f"[LATENCY] {name}: "
            f"{elapsed:.3f}s"
        )