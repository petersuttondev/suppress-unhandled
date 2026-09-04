from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Iterable
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


def test_suppress_keyboard_interrupt_raise_group() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        raise_='keyboard-interrupt',
        raise_group=True,
    )
    assert proc.failed
    assert proc.traceback_for(KeyboardInterrupt)


def test_inspect_groups_raise_group() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        inspect_groups=True,
        raise_='keyboard-interrupt',
        raise_group=True,
    )
    assert proc.failed
    assert not proc.stderr


def test_inspect_groups_raise_group_with_value_error() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        inspect_groups=True,
        raise_=('keyboard-interrupt', 'value-error'),
        raise_group=True,
    )
    assert proc.failed
    assert proc.traceback_for(ValueError)


def test_inspect_groups_suppress_both_raise_group() -> None:
    proc = _run_child(
        suppress=('keyboard-interrupt', 'value-error'),
        inspect_groups=True,
        raise_=('keyboard-interrupt', 'value-error'),
        raise_group=True,
    )
    assert proc.failed
    assert not proc.stderr


def test_inspect_groups_raise_nested_group() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        inspect_groups=True,
        raise_='keyboard-interrupt',
        raise_group=True,
        nest=True,
    )
    assert proc.failed
    assert not proc.stderr


def test_inspect_groups_raise_nested_group_with_value_error() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        inspect_groups=True,
        raise_=('keyboard-interrupt', 'value-error'),
        raise_group=True,
        nest=True,
    )
    assert proc.failed
    assert proc.traceback_for(ValueError)


def test_inspect_groups_raise_keyboard_interrupt() -> None:
    proc = _run_child(
        suppress='keyboard-interrupt',
        inspect_groups=True,
        raise_='keyboard-interrupt',
    )
    assert proc.failed
    assert not proc.stderr


def test_inspect_groups_raise_group_outside() -> None:
    proc = _run_child(
        suppress='value-error',
        inspect_groups=True,
        raise_='keyboard-interrupt',
        raise_group=True,
    )
    assert proc.failed
    assert proc.traceback_for(KeyboardInterrupt)


# ---------------------------------------------------------------------------- #

_ExceptionID: TypeAlias = Literal[
    'keyboard-interrupt',
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
        name = re.escape(exception.__name__)
        pattern = rf'^(\s*\+?\s*\|\s*)?{name}(:.*)?$'
        return re.search(pattern, self.stderr, re.MULTILINE) is not None


def _run_child(
    suppress: Iterable[_ExceptionID] | _ExceptionID | None = None,
    inspect_groups: bool = False,
    raise_: Iterable[_ExceptionID] | _ExceptionID | None = None,
    raise_group: bool = False,
    nest: bool = False,
) -> _RunChildResult:
    args = [sys.executable, __file__, '--child']
    if suppress is not None:
        if isinstance(suppress, str):
            suppress = (suppress,)
        for s in suppress:
            args += '--suppress', s
    if inspect_groups:
        args.append('--inspect-groups')
    if raise_ is not None:
        if isinstance(raise_, str):
            raise_ = (raise_,)
        for r in raise_:
            args += '--raise', r
    if raise_group:
        args.append('--raise-group')
    if nest:
        args.append('--nest')
    proc = subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
    )
    return _RunChildResult(proc.returncode, proc.stderr.strip())


def _create_exception(id: _ExceptionID) -> BaseException:
    match id:
        case 'keyboard-interrupt':
            return KeyboardInterrupt()
        case 'value-error':
            return ValueError()


def _child() -> None:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--child', action='store_true')

    choices: Final[tuple[_ExceptionID, ...]] = (
        'keyboard-interrupt',
        'value-error',
    )

    parser.add_argument(
        '--suppress',
        nargs='*',
        default=(),
        choices=choices,
    )

    parser.add_argument('--inspect-groups', action='store_true')
    parser.add_argument(
        '--raise',
        nargs='+',
        default=(),
        choices=choices,
        dest='raise_',
    )
    parser.add_argument('--raise-group', action='store_true')
    parser.add_argument('--nest', action='store_true')
    args = parser.parse_args()

    if not args.child:
        return

    exceptions = tuple(type(_create_exception(id)) for id in args.suppress)
    suppress_unhandled(*exceptions, inspect_groups=args.inspect_groups)

    if not args.raise_:
        return

    if not args.raise_group:
        assert len(args.raise_) == 1
        raise _create_exception(args.raise_[0])

    group = BaseExceptionGroup(
        'inner',
        tuple(_create_exception(id) for id in args.raise_),
    )

    if args.nest:
        group = BaseExceptionGroup('outer', (group,))

    raise group


if __name__ == '__main__':
    _child()
