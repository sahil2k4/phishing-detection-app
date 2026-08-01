import sys
import types

try:
    import fcntl  # type: ignore
except ModuleNotFoundError:
    class _DummyFcntl(types.ModuleType):
        def __getattr__(self, name):
            def _missing(*args, **kwargs):
                return None
            return _missing

    module = _DummyFcntl("fcntl")
    sys.modules["fcntl"] = module
