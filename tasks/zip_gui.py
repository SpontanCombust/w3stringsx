import os
from pathlib import Path
import subprocess
import zipfile
import zlib

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))
ORIG_CWD = os.getcwd()

GUI_DIR = os.path.join(ROOT, 'packages', 'gui')
GUI_ARTIFACT = os.path.join(GUI_DIR, 'dist', 'w3stringsx_gui')
TARGET_DIR = os.path.join(ROOT, 'dist')
TARGET_ZIP = os.path.join(TARGET_DIR, 'w3stringsx_gui.zip')
# pyinstaller doesn't filter out unused DLLs
FILE_BLACKLIST = [
    # pyside6-addon
    'Qt6Quick3D.dll',
    'Qt6Quick3D*.dll',
    'Qt6AxContainer.dll',
    'Qt6Bluetooth.dll',
    'Qt6Charts.dll',
    'Qt6DataVisualization.dll',
    'Qt6Graphs.dll',
    'Qt6GraphsWidgets.dll',
    'Qt6Multimedia.dll',
    'Qt6MultimediaWidgets.dll',
    'Qt6NetworkAuth.dll',
    'Qt6Nfc.dll',
    'Qt6Positioning.dll',
    'Qt6Quick3D.dll',
    'Qt6RemoteObjects.dll',
    'Qt6Scxml.dll',
    'Qt6Sensors.dll',
    'Qt6SerialPort.dll',
    'Qt6SerialBus.dll',
    'Qt6SpatialAudio.dll',
    'Qt6StateMachine.dll',
    'Qt6TextToSpeech.dll',
    'Qt6VirtualKeyboard.dll',
    'Qt6Web*.dll',
    'Qt6Pdf*.dll',
    'Qt6HttpServer.dll',
    'Qt6Location.dll',
    'Qt6Asyncio.dll',
    'Qt6WebView.dll',
]

if not os.path.isdir(TARGET_DIR):
    os.mkdir(TARGET_DIR)
    print('Created output directory ' + TARGET_DIR)

os.chdir(GUI_DIR)
# make sure the packages are setup
subprocess.run('uv sync', check=True, shell=True)
# use pyinstaller to pack the project into distributable standalone format
subprocess.run('uvx pyinstaller -y w3stringsx_gui.spec', check=True, shell=True)
# zip it up
with zipfile.ZipFile(TARGET_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=zlib.Z_DEFAULT_COMPRESSION) as zip:
    for root, dirs, files in os.walk(GUI_ARTIFACT):
        root_rel = os.path.relpath(root, GUI_ARTIFACT)
        for file in files:
            file_rel = os.path.join(root_rel, file)
            if not any([Path(file_rel).match(pat) for pat in FILE_BLACKLIST]):
                # print(file_rel)
                file_full = os.path.join(root, file)
                zip.write(file_full, file_rel)

print('w3stringsx GUI has been successfully packaged to ' + TARGET_ZIP)

os.chdir(ORIG_CWD)