"""Windows compatibility shim for the POSIX-only `fcntl` module.

The Index Hub api_client.py imports `fcntl` at module scope to lock its local
cache file. Windows Python has no `fcntl`, so the import raises
ModuleNotFoundError and the client cannot run at all.

This shim resolves the genuine stdlib module whenever it exists (POSIX), and
only degrades to no-op locking when it does not (Windows). Single-user local
caching does not need cross-process locking, so no-op is safe there.

Drop-in placement: <skill>/scripts/fcntl.py
Re-apply after the skill package is updated or reinstalled.
"""

import os
import sys

__all__ = ["flock", "lockf", "ioctl", "LOCK_EX", "LOCK_NB", "LOCK_SH", "LOCK_UN"]

# Remove this shim from sys.modules so `import fcntl` below can find the real
# stdlib module instead of re-entering ourselves.
_self = sys.modules.pop(__name__, None)
_shim_dir = os.path.dirname(os.path.abspath(__file__))
_saved_path = sys.path[:]
_real = None

try:
    # Hide the shim directory so the stdlib copy wins on POSIX.
    sys.path[:] = [
        p for p in _saved_path if os.path.abspath(p or os.curdir) != _shim_dir
    ]
    try:
        import fcntl as _real  # noqa: F401  (genuine stdlib module)
    except ImportError:
        _real = None
finally:
    sys.path[:] = _saved_path

if _real is not None:
    # Re-export the genuine module so callers get real advisory locking.
    for _name in dir(_real):
        if not _name.startswith("__"):
            globals()[_name] = getattr(_real, _name)
    sys.modules[__name__] = _real
else:
    LOCK_SH = 0x1
    LOCK_EX = 0x2
    LOCK_NB = 0x4
    LOCK_UN = 0x8

    def flock(fd, operation):
        """No-op: Windows has no POSIX advisory file locking."""
        return None

    def lockf(fd, operation, length=0, start=0, whence=0):
        """No-op: see flock()."""
        return None

    def ioctl(fd, request, arg=0, mutate_flag=True):
        """Unavailable on Windows; kept so imports do not fail."""
        raise OSError("fcntl.ioctl is not available on this platform")

    # Restore this shim in sys.modules: importlib pops and re-inserts the
    # module by name after exec_module, and would raise KeyError if absent.
    # _self is this module object, so its __dict__ already holds the no-ops.
    if _self is not None:
        sys.modules[__name__] = _self
