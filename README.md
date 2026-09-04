# suppress-unhandled

Suppress traceback of specified unhandled exceptions, preserve everything else.

```Python
from suppress_unhandled import suppress_unhandled

suppress_unhandled(KeyboardInterrupt)
input('Pause')
```

```ShellSession
$ python example.py
Pause ^C
$
```

## Install

```
pip install suppress-unhandled
```

## Exception groups

Pass `inspect_groups` to also suppress a group whose contents, however deeply
nested, are all being suppressed:

```Python
import asyncio
from suppress_unhandled import suppress_unhandled

suppress_unhandled(ValueError, inspect_groups=True)

async def some_task():
    raise ValueError('oh no!')

async def main():
    async with asyncio.TaskGroup() as group:
        group.create_task(some_task())
        group.create_task(some_task())

asyncio.run(main())
```

```ShellSession
$ python example.py
$
```

`asyncio.TaskGroup` collects both failures into an `ExceptionGroup`, which
`suppress_unhandled(ValueError)`, without `inspect_groups=True`, will not match:

```ShellSession
$ python example.py
  + Exception Group Traceback (most recent call last):
  ...
  | ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | ValueError: oh no!
    +---------------- 2 ----------------
    | ValueError: oh no!
    +------------------------------------
```

Groups containing anything else are not suppressed and their tracebacks print.

## Background

`Ctrl+C` is often the normal way to exit a Python program. By default, Python
prints a scary-looking traceback to the stderr:

```ShellSession
$ python example.py
^CTraceback (most recent call last):
  File "/tmp/example.py", line 1, in <module>
    do_something_forever()
    ~~~~~~~~~~~~~~~~~~~~^^
KeyboardInterrupt
```

You could `suppress` `KeyboardInterrupt`:

```Python
from contextlib import suppress

with suppress(KeyboardInterrupt):
    do_something_forever()
```

The traceback is gone, but the return code is wrong and, if you add code after
the `with` block, it'll get run! There's also all [this](https://github.com/python/cpython/blob/b32c830d444c85421bd2c0c7af494c9d85485a29/Modules/main.c#L727)
complex behaviour that gets suppressed.
