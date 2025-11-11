from abc import ABC, abstractmethod
from typing import TypeVar, Generic


T = TypeVar('T')
class ConfigurationValue(Generic[T]):
    __value: T | None

    def __init__(self, value: T | None = None) -> None:
        self.__value = value

    def get(self) -> T | None:
        return self.__value
    
    def get_required(self) -> T:
        if self.__value is None:
            raise Exception('Configuration value not defined')
        return self.__value
    
    def is_some(self) -> bool:
        return self.__value is not None
    
    def is_none(self) -> bool:
        return self.__value is None
    
class Configuration(ABC):
    def some(self, v: T) -> ConfigurationValue[T]:
        return ConfigurationValue(v)
    
    def none(self) -> ConfigurationValue[T]: # pyright: ignore[reportInvalidTypeVarUse]
        return ConfigurationValue(None)

    @property
    @abstractmethod
    def app_dir(self) -> ConfigurationValue[str]:
        return self.none()
    
    @property
    @abstractmethod
    def app_version(self) -> ConfigurationValue[str]:
        return self.none()

    @property
    @abstractmethod
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.none()

    @abstractmethod
    def reset_to_default(self):
        ...

    def initialize(self):
        if self.app_version.is_none():
            self.reset_to_default()