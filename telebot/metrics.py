import contextlib
import time
from typing import Generator, Optional, TypedDict

from typing_extensions import Required


class TelegramUpdateMetrics(TypedDict, total=False):
    bot_prefix: Required[str]
    update_id: Required[int]
    received_at: Required[float]  # UNIX timestamp

    update_type_name: str
    matched_handler_name: Optional[str]  # None = no handler matched, update ignored

    handler_test_durations: list[float]  # list of durations for each handler tested
    processing_duration: float

    exception_type: str


@contextlib.contextmanager
def save_handler_test_duration(metrics: TelegramUpdateMetrics) -> Generator[None, None, None]:
    start_time = time.time()
    try:
        yield
    finally:
        metrics.setdefault("handler_test_durations", []).append(time.time() - start_time)


@contextlib.contextmanager
def save_processing_duration(metrics: TelegramUpdateMetrics) -> Generator[None, None, None]:
    start_time = time.time()
    try:
        yield
    finally:
        metrics["processing_duration"] = time.time() - start_time
