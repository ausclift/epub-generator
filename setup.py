from setuptools import setup

APP = ['ePUBGenerator.py']
DATA_FILES = ['icon.jpg']

setup(
    app=APP,
    data_files=DATA_FILES,
    setup_requires=['py2app'],
    options={
        'py2app': {
            'iconfile': 'icon.jpg',
            'packages': ['PIL', 'natsort'],
            'excludes': ['numpy', 'tkinter.test', 'PIL.tests', 'unittest'],
        }
    },
)
