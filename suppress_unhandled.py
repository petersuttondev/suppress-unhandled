from __future__ import annotations
import sys as _sys
from typing import TYPE_CHECKING as _TYPE_CHECKING


if _TYPE_CHECKING:
    from types import TracebackType as _TracebackType
    from typing import Final as _Final


__all__: _Final = ('suppress_unhandled',)


def suppress_unhandled(*exceptions: type[BaseException]) -> None:
    """Suppress traceback of specified unhandled exceptions

    More precisely, replaces sys.excepthook and forwards all but the
    specified unhandled exceptions to the previous hook.

        suppress_unhandled(ValueError)
        raise ValueError()
        # Python will fail as normal but a traceback will not be
        # printed to the stderr

    This cannot be undone. You should probably only call this onces per
    execution.
    """
    prev_excepthook = _sys.excepthook

    def excepthook(
        type: type[BaseException],
        value: BaseException,
        traceback: _TracebackType | None,
    ) -> object:
        if not isinstance(value, exceptions):
            return prev_excepthook(type, value, traceback)

    _sys.excepthook = excepthook
