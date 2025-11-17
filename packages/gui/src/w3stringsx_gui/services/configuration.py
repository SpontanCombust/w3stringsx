import importlib.metadata
import logging
import os
from typing import Any, TypeVar

import flet as ft

from w3stringsx_svc.configuration import Configuration, ConfigurationValue


_T = TypeVar('_T')

class W3stringsxGuiConfiguration(Configuration):
    def __init__(self, 
        page: ft.Page
    ):
        self.__page = page


    @property
    def app_dir(self) -> ConfigurationValue[str]:
        path = __file__
        # climb back to services < w3stringsx_gui < src < gui
        for i in range(4):
            path = os.path.dirname(path)
        return self.some(path)
    
    @property
    def app_version(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.app_version', importlib.metadata.version('w3stringsx-gui'))
    
    @app_version.setter
    def app_version(self, val: str):
        self.__set('w3stringsx_gui.app_version', val)

    @property
    def log_level(self) -> ConfigurationValue[int]:
        return self.__get('w3stringsx_gui.log_level', logging.INFO)
    
    @log_level.setter
    def log_level(self, val: int | None):
        self.__set('w3stringsx_gui.log_level', val)

    @property
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.w3strings_encoder_path', None)
    
    @w3strings_encoder_path.setter
    def w3strings_encoder_path(self, val: str | None):
        self.__set('w3stringsx_gui.w3strings_encoder_path', val)

    @property
    def default_fallback_language(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.default_fallback_language', 'en')
    
    @default_fallback_language.setter
    def default_fallback_language(self, val: str | None):
        self.__set('w3stringsx_gui.default_fallback_language', val)
    

    @property
    def theme_mode(self) -> ConfigurationValue[str]:
        return self.__get('w3stringsx_gui.theme_mode', ft.ThemeMode.SYSTEM.value)
    
    @theme_mode.setter
    def theme_mode(self, val: str | None):
        self.__set('w3stringsx_gui.theme_mode', val)

    @property
    def logs_panel_scrollback(self) -> ConfigurationValue[int]:
        return self.__get('w3stringsx_gui.logs_panel_scrollback', 1000)
    
    @logs_panel_scrollback.setter
    def logs_panel_scrollback(self, val: int | None):
        self.__set('w3stringsx_gui.logs_panel_scrollback', val)


    def reset_to_default(self):
        client_storage = self.__page.client_storage
        for key in client_storage.get_keys("w3stringsx_gui."):
            client_storage.remove(key)
    

    def __get(self, key: str, default: _T | None) -> ConfigurationValue[_T]:
        val = self.__page.client_storage.get(key)
        if val is None:
            return self.none(default)
        return self.some(val)
    
    def __set(self, key: str, val: Any):
        client_storage = self.__page.client_storage
        if bool(val):
            client_storage.set(key, val)
        else:
            # remove falsy values
            client_storage.remove(key)
