from setuptools import setup

APP = ['generate_epub.py']
DATA_FILES = ['icon.jpg']

setup(
    name='ePUB Generator',
    version='0.2',
    app=APP,
    data_files=DATA_FILES,
    setup_requires=['py2app'],
    options={
        'py2app': {
            'iconfile': 'icon.jpg',
            'packages': ['PIL', 'natsort', 'tkinter'],
        }
    },
)
