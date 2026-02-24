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
