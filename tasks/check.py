import os
import subprocess

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
ORIG_CWD = os.getcwd()

PACKAGES_DIR = os.path.join(ROOT, 'packages')

packages_needing_fixes = []
with os.scandir(PACKAGES_DIR) as it:
    for entry in it:
        if entry.is_dir() and not entry.name.startswith('.'):
            package_dir = entry.path
            package_name = entry.name
            # move to the package directory
            os.chdir(package_dir)

            print("Checking package", package_name)

            sync_cmd = 'uv sync'
            # lock files of libraries do not get stored in version control 
            if os.path.exists(os.path.join(package_dir, 'uv.lock')):
                # if lockfile already exists, make sure venv is created exactly according to it
                sync_cmd += ' --locked'
            subprocess.run(sync_cmd, shell=True, check=True)
            # lint using ruff
            ruff_proc = subprocess.run('uvx ruff check', shell=True)
            # type-check using ty
            ty_proc = subprocess.run('uvx ty check', shell=True)

            if ruff_proc.returncode != 0 or ty_proc.returncode != 0:
                packages_needing_fixes.append(package_name)
            print('\n\n')

os.chdir(ORIG_CWD)

if len(packages_needing_fixes) > 0:
    print("Following packages require attention:", packages_needing_fixes)
    exit(1)
else:
    print("Checks passed for all packages!")
    exit(0)