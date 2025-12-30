from setuptools import setup

APP = ['ePUBNeko.py']
OPTIONS = {
    'packages': ['PIL', 'natsort'],
    'excludes': ['numpy', 'tkinter.test', 'PIL.tests', 'unittest'],
    'iconfile': 'icon.png',
    'includes': ['os', 'threading', 'time', 'zipfile', 'shutil', 'uuid', 'tkinter', 'datetime', 'pathlib'],
    'plist': {
        'CFBundleName': 'ePUB Neko',
        'CFBundleDisplayName': 'ePUB Neko',
        'CFBundleIdentifier': 'com.heathx.epubneko',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)