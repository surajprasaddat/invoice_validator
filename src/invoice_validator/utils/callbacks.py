from typing import Callable, Optional

_progress_cb: Optional[Callable[[float], None]] = None
_add_log_cb: Optional[Callable[[str], None]] = None


def set_callbacks(progress: Callable[[float], None], add_log: Callable[[str], None]) -> None:
    global _progress_cb, _add_log_cb
    _progress_cb = progress
    _add_log_cb = add_log


def progress(value: float, desc: str = "") -> None:
    if _progress_cb:
        try:
            _progress_cb(value, desc=desc)
        except TypeError:
            # Fallback for callbacks without desc kwarg
            _progress_cb(value)


def add_log(message: str) -> None:
    if _add_log_cb:
        _add_log_cb(message)
