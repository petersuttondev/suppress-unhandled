from __future__ import annotations as _annotations

import sys as _sys
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from types import TracebackType as _TracebackType
    from typing import Final as _Final


__all__: _Final = ('suppress_unhandled',)


def _suppress(
    value: BaseException,
    exceptions: tuple[type[BaseException], ...],
    inspect_groups: bool,
) -> bool:
    return isinstance(value, exceptions) or (
        inspect_groups
        and isinstance(value, BaseExceptionGroup)
        and all(
            _suppress(child, exceptions, inspect_groups)
            for child in value.exceptions
        )
    )


def suppress_unhandled(
    *exceptions: type[BaseException],
    inspect_groups: bool = False,
) -> None:
    """Suppress traceback of specified unhandled exceptions

    More precisely, replaces sys.excepthook and forwards all but the
    specified unhandled exceptions to the previous hook.

        suppress_unhandled(ValueError)
        raise ValueError()
        # Python will fail as normal but a traceback will not be
        # printed to the stderr

    If inspect_groups is true, an unhandled exception group is
    suppressed when every exception it contains, however deeply nested,
    is one of the specified exceptions.

        suppress_unhandled(ValueError, inspect_groups=True)
        raise ExceptionGroup('', [ValueError()])
        # Suppressed as well

    Suppression cannot be undone. You should probably only call this
    once per execution.
    """
    prev_excepthook = _sys.excepthook

    def excepthook(
        type: type[BaseException],
        value: BaseException,
        traceback: _TracebackType | None,
    ) -> object:
        if not _suppress(value, exceptions, inspect_groups):
            return prev_excepthook(type, value, traceback)

    _sys.excepthook = excepthook
