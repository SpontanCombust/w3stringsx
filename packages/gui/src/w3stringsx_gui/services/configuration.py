import os
from typing import Any

from w3stringsx_svc.configuration import Configuration, ConfigurationValue
from w3stringsx_gui.services.page_provider import PageProvider


class W3stringsxGuiConfiguration(Configuration):
    def __init__(self, 
        page_provider: PageProvider
    ):
        self.__page_provider = page_provider


    @property
    def app_dir(self) -> ConfigurationValue[str]:
        return self.some(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    @property
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.w3strings_encoder_path')
    
    @w3strings_encoder_path.setter
    def w3strings_encoder_path(self, val: str):
        self.__set('w3stringsx_gui.w3strings_encoder_path', val)
    
    @property
    def theme_mode(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.theme_mode')
    
    @theme_mode.setter
    def theme_mode(self, val: str):
        self.__set('w3stringsx_gui.theme_mode', val)


    def __get(self, key: str) -> ConfigurationValue[Any]:
        val = self.__page_provider.provide().client_storage.get(key)
        if val is None:
            return self.none()
        return self.some(val)
    
    def __set(self, key: str, val: Any):
        self.__page_provider.provide().client_storage.set(key, val)