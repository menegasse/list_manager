from typing import Any, Callable, Generic, TypeVar, overload

from django.conf import settings
from django.db import models, transaction
from django.db.models import signals
from typing_extensions import Concatenate, ParamSpec

_S = TypeVar("_S", bound="ModelHookField[Any, Any, Any]")
_T = TypeVar("_T", bound=models.Model)
_R = TypeVar("_R")
_P = ParamSpec("_P")
_hooks_cache: dict[Callable, Callable] = {}


class ModelHook(Generic[_T, _P, _R]):
    """Model hook."""

    def __init__(self, f: Callable[Concatenate[_T, _P], _R], obj: _T):
        super().__init__()
        self._f = f
        self._obj = obj

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        return self._f(self._obj, *args, **kwargs)


class ModelHookField(Generic[_T, _P, _R]):
    """Model task field."""

    def __init__(
        self,
        f: Callable[Concatenate[_T, _P], _R],
        signal: signals.ModelSignal,
        *,
        on_commit: bool = False,
    ):
        super().__init__()
        self._f = f
        self._name = None
        self._signal = signal
        self._on_commit = on_commit
        self._registered = set()

    def __set_name__(self, owner: type[_T], name: str):
        self._name = name
        self._signal.connect(self._callback, sender=owner)
        self._registered.add(owner)

    @overload
    def __get__(self, obj: _T, cls: type[_T]) -> ModelHook[_T, _P, _R]:
        ...

    @overload
    def __get__(self: _S, obj: None, cls: type[_T]) -> _S:
        ...

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        c = obj.__dict__.get(self._name, None)
        if c is None:
            c = ModelHook(f=self._f, obj=obj)
            obj.__dict__[self._name] = c

        return c

    def _callback(self, sender: type[_T], instance: _T, *args, **kwargs):
        if self._on_commit and not settings.RUNNING_TESTS:
            transaction.on_commit(lambda: self._f(instance, *args, **kwargs))
        else:
            self._f(instance, *args, **kwargs)

    def register(self, cls: type[_T]):
        if cls in self._registered:
            return

        self._signal.connect(self._callback, sender=cls)
        self._registered.add(cls)


def _hook(signal: signals.ModelSignal):
    @overload
    def hook(f: Callable[Concatenate[_T, _P], _R], /) -> ModelHookField[_T, _P, _R]:
        ...

    @overload
    def hook(
        f: None = ...,
        on_commit: bool = False,
    ) -> Callable[[Callable[Concatenate[_T, _P], _R]], ModelHookField[_T, _P, _R]]:
        ...

    def hook(f=None, /, on_commit=False) -> Any:
        def wrapper(f):
            return ModelHookField(f, signal, on_commit=on_commit)

        if f is not None:
            return wrapper(f)

        return wrapper

    return hook


pre_save = _hook(signals.pre_save)
post_save = _hook(signals.post_save)
pre_delete = _hook(signals.pre_delete)
post_delete = _hook(signals.post_delete)
