import os

W3STRINGSX_VERSION = '2.0.0'
"""
Path to the packaged executable file running the CLI or GUI.
It is not referring to literal .exe file, but to a python archive effectively acting like an executable, i.e. .pyz or .pyzw.
Purpose of this is mainly to access the parent directory of said executable.   
"""
W3STRINGSX_EXE_PATH = os.path.dirname(os.path.dirname(__file__))