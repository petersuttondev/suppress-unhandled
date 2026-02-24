from __future__ import annotations
from collections.abc import Iterable
import subprocess
import sys
from typing import Final, Literal, NamedTuple, TypeAlias, final
from suppress_unhandled import suppress_unhandled


def test_suppress_keyboard_interrupt() -> None:
    proc = _run_child(suppress='keyboard-interrupt')
    assert proc.succeeded
    assert not proc.stderr


def test_raise_keyboard_interrupt_outside() -> None:
    proc = _run_child(raise_='keyboard-interrupt')
    assert proc.failed
    assert proc.traceback_for(KeyboardInterrupt)


def test_suppress_keyboard_interrupt_raise_keyboard_interrupt() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        raise_='keyboard-interrupt',
    )

    assert proc.failed
    assert not proc.stderr


def test_suppress_keyboard_interrupt_raise_value_error() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        raise_='value-error',
    )
    assert proc.failed
    assert proc.traceback_for(ValueError)


def test_suppress_keyboard_interrupt_and_value_error_raise_keyboard_interrupt() -> (
    None
):
    proc = _run_child(
        suppress=('keyboard-interrupt', 'value-error'),
        raise_='keyboard-interrupt',
    )
    assert proc.failed
    assert proc.traceback_for(KeyboardInterrupt)


def test_suppress_keyboard_interrupt_and_value_error_raise_value_error() -> (
    None
):
    proc = _run_child(
        suppress=('keyboard-interrupt', 'value-error'),
        raise_='value-error',
    )
    assert proc.failed
    assert not proc.stderr


# ---------------------------------------------------------------------------- #

_ExceptionID: TypeAlias = Literal[
    'keyboard-interrupt',
    'system-exit',
    'value-error',
]


@final
class _RunChildResult(NamedTuple):
    returncode: int
    stderr: str

    @property
    def failed(self) -> bool:
        return self.returncode != 0

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def traceback_for(self, exception: type[BaseException]) -> bool:
        return self.stderr.endswith(exception.__name__)


def _run_child(
    suppress: Iterable[_ExceptionID] | _ExceptionID | None = None,
    raise_: _ExceptionID | None = None,
) -> _RunChildResult:
    args = [sys.executable, __file__, '--child']
    if suppress is not None:
        if isinstance(suppress, str):
            suppress = (suppress,)
        for s in suppress:
            args += '--suppress', s
    if raise_ is not None:
        args += '--raise', raise_
    proc = subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    return _RunChildResult(proc.returncode, proc.stderr.strip())


def _child() -> None:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--child', action='store_true')

    choices: Final[tuple[_ExceptionID, ...]] = (
        'keyboard-interrupt',
        'system-exit',
        'value-error',
    )

    parser.add_argument(
        '--suppress',
        nargs='*',
        default=(),
        choices=choices,
    )

    parser.add_argument('--raise', choices=choices, dest='raise_')
    args = parser.parse_args()

    if not args.child:
        return

    exceptions: list[type[BaseException]] = []

    for suppress in args.suppress:
        match suppress:
            case 'keyboard-interrupt':
                exceptions.append(KeyboardInterrupt)
            case 'system-exit':
                exceptions.append(SystemError)
            case 'value-error':
                exceptions.append(ValueError)

    suppress_unhandled(*exceptions)

    match args.raise_:
        case 'keyboard-interrupt':
            raise KeyboardInterrupt()
        case 'system-exit':
            raise SystemError(1)
        case 'value-error':
            raise ValueError()


if __name__ == '__main__':
    _child()
