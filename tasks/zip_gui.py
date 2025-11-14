import os
import subprocess
import zipfile
import zlib

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
ORIG_CWD = os.getcwd()

GUI_DIR = os.path.join(ROOT, 'packages', 'gui')
GUI_ARTIFACT_DIR = os.path.join(GUI_DIR, 'build', 'windows')
TARGET_DIR = os.path.join(ROOT, 'dist')
TARGET_ZIP = os.path.join(TARGET_DIR, 'w3stringsx_gui.zip')

if not os.path.isdir(TARGET_DIR):
    os.mkdir(TARGET_DIR)
    print('Created output directory ' + TARGET_DIR)

os.chdir(GUI_DIR)
# make sure the packages are setup
subprocess.run('uv sync --locked', check=True, shell=True)
# use pyinstaller to pack the project into distributable standalone format
subprocess.run('uv run --no-sync --no-editable task build-windows', check=True, shell=True)
# zip it up
with zipfile.ZipFile(TARGET_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=zlib.Z_DEFAULT_COMPRESSION) as zip:
    for root, dirs, files in os.walk(GUI_ARTIFACT_DIR):
        root_rel = os.path.relpath(root, GUI_ARTIFACT_DIR)
        for file in files:
            file_full = os.path.join(root, file)
            file_rel = os.path.join(root_rel, file)
            zip.write(file_full, file_rel)
                

print('w3stringsx GUI has been successfully packaged to ' + TARGET_ZIP)

os.chdir(ORIG_CWD)