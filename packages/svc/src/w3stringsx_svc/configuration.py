from typing import Protocol, TypeVar, Generic


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
    
class Configuration(Protocol):
    def some(self, v: T) -> ConfigurationValue[T]:
        return ConfigurationValue(v)
    
    def none(self) -> ConfigurationValue[T]: # pyright: ignore[reportInvalidTypeVarUse]
        return ConfigurationValue(None)

    @property
    def app_dir(self) -> ConfigurationValue[str]:
        return self.none()

    @property
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.none()

