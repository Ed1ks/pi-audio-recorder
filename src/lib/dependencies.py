import subprocess
from importlib import import_module


def install_all_dependencies_if_not_exists():
    print('Check all Dependencies are installed...')
    dependencies = ['pynput', 'pyaudio', 'gpiozero', 'easywebdav']
    for d in dependencies:
        import_or_install(d)
    print('Done')


def import_or_install(package):
    try:
        import_module(package)
    except ImportError:
        subprocess.call(f"sudo apt -y install python3-{package}", shell=True)
        # import pip
        # pip.main(['install', package])
