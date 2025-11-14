import os
import subprocess
import zipfile
import zlib

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
ORIG_CWD = os.getcwd()

CLI_DIR = os.path.join(ROOT, 'packages', 'cli')
CLI_ARTIFACT = os.path.join(CLI_DIR, 'dist', 'w3stringsx.exe')
TARGET_DIR = os.path.join(ROOT, 'dist')
TARGET_ZIP = os.path.join(TARGET_DIR, 'w3stringsx.zip')


if not os.path.isdir(TARGET_DIR):
    os.mkdir(TARGET_DIR)
    print('Created output directory ' + TARGET_DIR)

os.chdir(CLI_DIR)
# make sure the packages are setup
subprocess.run('uv sync --locked', check=True, shell=True)
# use pyinstaller to pack the project into standalone executable
subprocess.run('uv run --no-sync --no-editable task build', check=True, shell=True)
# zip it up
with zipfile.ZipFile(TARGET_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=zlib.Z_DEFAULT_COMPRESSION) as zip:
    zip.write(CLI_ARTIFACT, os.path.basename(CLI_ARTIFACT))

print('w3stringsx CLI has been successfully packaged to ' + TARGET_ZIP)

os.chdir(ORIG_CWD)