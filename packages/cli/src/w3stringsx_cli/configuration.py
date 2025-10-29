import os

from w3stringsx_svc.configuration import Configuration, ConfigurationValue


class W3stringsxCliConfiguration(Configuration):
    def __init__(self):
        pass

    @property
    def app_dir(self) -> ConfigurationValue[str]:
        return self.some(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    @property
    def w3strings_encoder_path(self) -> ConfigurationValue[str]:
        return self.none()
