"""
!!! WARNING !!!
Voodoo metaprogramming, argument-juggling magic incoming!
"""

from __future__ import annotations
import inspect
import pprint
from typing import Protocol, TypeVar, Type, Callable, Self, Any, cast, get_type_hints, Generic


__all__ = [
    "ServiceResolver",
    "Injected",
    "ServiceContainer",
    "di"
]


T = TypeVar('T')
U = TypeVar('U')


class ServiceResolver(Protocol):
    def resolve(self, cls: Type[T]) -> T:
        raise NotImplementedError()


class _ServiceProvider(Protocol):
    def provide(self, **kwargs: Any) -> object:
        raise NotImplementedError()
    
    def impl_type(self) -> Type[Any]:
        raise NotImplementedError()

class _ObjectServiceProvider(_ServiceProvider, Generic[T]):
    def __init__(self, cls: Type[T], obj: T) -> None:
        self._impl_type: Type[T] = cls
        self.obj = obj

    def provide(self, **kwargs: Any) -> T:
        return self.obj
    
    def impl_type(self) -> Type[Any]:
        return self._impl_type
    
class _CallableServiceProvider(_ServiceProvider, Generic[T]):
    def __init__(self, cls: Type[T], callable: Callable[..., T]) -> None:
        self._impl_type = cls
        self.callable = callable

    def provide(self, **kwargs: Any) -> T:
        return self.callable(**kwargs)
    
    def impl_type(self) -> Type[Any]:
        return self._impl_type

class _MemoizedCallableServiceProvider(_CallableServiceProvider[T]):
    def __init__(self, cls: Type[T], callable: Callable[..., T]) -> None:
        super().__init__(cls, callable)
        self.memoized: T | None = None

    def provide(self, **kwargs: Any) -> T:
        if self.memoized is None:
            self.memoized = self.callable(**kwargs)
        return self.memoized


class Injected(Generic[T]):
    def __init__(self, resolution: Callable[[], T]) -> None:
        self.__resolution = resolution

    def resolve(self) -> T:
        return self.__resolution()


class ServiceContainer(ServiceResolver):
    def __init__(self) -> None:
        self.__providers: dict[Type[Any], _ServiceProvider] = {}

    @staticmethod
    def builder() -> ServiceContainerBuilder:
        return ServiceContainerBuilder()

    def add_provider(self, cls: Type[Any], svc_provider: _ServiceProvider):
        self.__providers[cls] = svc_provider

    def override(self, other: Self):
        self.__providers.update(other.__providers)

    def resolve(self, cls: Type[T]) -> T:
        provider = self.__providers.get(cls)
        if provider is None:
            raise Exception('Service %s.%s is not registered' % (cls.__module__, cls.__name__))
        injections = self.__resolve_dependencies(provider.impl_type())
        obj = provider.provide(**injections)
        return cast(T, obj)
    
    def inject(self, cls: Type[T]) -> Injected[T]:
        return Injected(lambda: self.resolve(cls))
    
    def __resolve_dependencies(self, cls: Type[T]) -> dict[str, Any]:
        sig = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)

        # first get all params
        params_list = [item[1] for item in sig.parameters.items()]
        # move past self
        if params_list[0].name == 'self':
            params_list = params_list[1:]
        if len(params_list) == 0:
            return {}
        # try resolving the rest that can be injected
        injections: dict[str, Any] = {}
        for param in params_list:
            param_type: Type[Any] | None = type_hints.get(param.name)
            if param_type is not None:
                if param_type is cls:
                    raise Exception('Detected circular type dependence. Injections can not be resolved here')
                try:
                    svc = self.resolve(param_type)
                    injections[param.name] = svc
                except Exception as ex:
                    if param.default is not param.empty:
                        # depdendency couldn't be found, but there was a default argument available, so we can move on
                        continue
                    else:
                        # otherwise the resolution can't be completed
                        raise ex
            elif param.default is not param.empty:
                # leave this parameter as is
                continue
            else:
                raise Exception('Could not resolve an unannotated, non-default parameter: ' + param.name)            

        return injections
    
    def print_providers(self):
        pprint.pprint(self.__providers)
    
    

class ServiceContainerBuilder:
    def __init__(self) -> None:
        self.__container = ServiceContainer()

    def build(self) -> ServiceContainer:
        return self.__container

    def singleton(self, impl_cls: Type[T], obj: T | None = None) -> Self:
        if obj is None:
            provider = _MemoizedCallableServiceProvider(impl_cls, lambda **kwargs: impl_cls(**kwargs))
        else:
            provider = _ObjectServiceProvider(impl_cls, obj)
        self.__container.add_provider(impl_cls, provider)
        return self
    
    def singleton_factory(self, impl_cls: Type[T], factory: Callable[[ServiceResolver], T]) -> Self:
        provider = _MemoizedCallableServiceProvider(impl_cls, lambda **kwargs: factory(self.__container))
        self.__container.add_provider(impl_cls, provider)
        return self
    
    def abstract_singleton(self, base_cls: Type[T], impl_cls: Type[U], obj: U | None = None) -> Self:
        if obj is None:
            provider = _MemoizedCallableServiceProvider(impl_cls, lambda **kwargs: impl_cls(**kwargs))
        else:
            provider = _ObjectServiceProvider(impl_cls, obj)
        self.__container.add_provider(base_cls, provider)
        return self
    
    def abstract_singleton_factory(self, base_cls: Type[T], impl_cls: Type[U], factory: Callable[[ServiceResolver], U]) -> Self:
        provider = _MemoizedCallableServiceProvider(impl_cls, lambda **kwargs: factory(self.__container))
        self.__container.add_provider(base_cls, provider)
        return self
    
    def transitive(self, impl_cls: Type[T]) -> Self:
        provider = _CallableServiceProvider(impl_cls, lambda **kwargs: impl_cls(**kwargs))
        self.__container.add_provider(impl_cls, provider)
        return self
    
    def transitive_factory(self, impl_cls: Type[T], factory: Callable[[ServiceResolver], T]) -> Self:
        provider = _CallableServiceProvider(impl_cls, lambda **kwargs: factory(self.__container))
        self.__container.add_provider(impl_cls, provider)
        return self
    
    def abstract_transitive(self, base_cls: Type[T], impl_cls: Type[U]) -> Self:
        provider = _CallableServiceProvider(impl_cls, lambda **kwargs: impl_cls(**kwargs))
        self.__container.add_provider(base_cls, provider)
        return self
    
    def abstract_transitive_factory(self, base_cls: Type[T], impl_cls: Type[U], factory: Callable[[ServiceResolver], U]) -> Self:
        provider = _CallableServiceProvider(impl_cls, lambda **kwargs: factory(self.__container))
        self.__container.add_provider(base_cls, provider)
        return self
    


class DependencyInjection(ServiceResolver):
    def __init__(self) -> None:
        self.container: ServiceContainer = ServiceContainer()

    def resolve(self, cls: type[T]) -> T:
        return self.container.resolve(cls)
    
    def inject(self, cls: Type[T]) -> Injected[T]:
        return Injected(lambda: self.resolve(cls))
    
    def set_current(self, container: ServiceContainer):
        self.container = container


di = DependencyInjection()
