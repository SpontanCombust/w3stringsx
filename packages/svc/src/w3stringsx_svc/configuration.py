from abc import ABC, abstractmethod
from typing import TypeVar, Generic


T = TypeVar('T')
class ConfigurationValue(Generic[T]):
    __value: T | None
    __default: T | None

    def __init__(self, value: T | None = None, default: T | None = None) -> None:
        self.__value = value
        self.__default = default

    def get(self) -> T | None:
        return self.__value
    
    def get_or_default(self) -> T:
        if self.__value is not None:
            return self.__value
        elif self.__default is not None:
            return self.__default
        else:
            raise Exception('Configuration value does not have a default')
    
    def is_some(self) -> bool:
        return self.__value is not None
    
    def is_none(self) -> bool:
        return self.__value is None
    
class Configuration(ABC):
    def some(self, v: T) -> ConfigurationValue[T]:
        return ConfigurationValue(v)
    
    def none(self, default: T | None) -> ConfigurationValue[T]: # pyright: ignore[reportInvalidTypeVarUse]
        return ConfigurationValue(None, default)

    #TODO move out of config
    @property
    @abstractmethod
    def app_dir(self) -> ConfigurationValue[str]:
        ...
    
    @property
    @abstractmethod
    def app_version(self) -> ConfigurationValue[str]:
        ...

    @property
    @abstractmethod
    def log_level(self) -> ConfigurationValue[int]:
        ...

    @property
    @abstractmethod
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        ...


    @abstractmethod
    def reset_to_default(self):
        ...
