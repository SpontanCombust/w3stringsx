import importlib.metadata
import logging
import os

from w3stringsx_svc.configuration import Configuration, ConfigurationValue


# This implementation does not persist settings yet
class W3stringsxCliConfiguration(Configuration):
    def __init__(self):
        pass

    @property
    def app_dir(self) -> ConfigurationValue[str]:
        return self.some(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    @property
    def app_version(self) -> ConfigurationValue[str]:
        return self.none(importlib.metadata.version('w3stringsx-cli'))
    
    @property
    def log_level(self) -> ConfigurationValue[int]:
        return self.none(logging.INFO)
    
    @property
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.none(None)
    
    @property
    def default_fallback_language(self) -> ConfigurationValue[str]:
        return self.none('en')

    def reset_to_default(self):
        pass
