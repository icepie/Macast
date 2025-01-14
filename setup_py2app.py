"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

import os
import datetime
from setuptools import setup

APP = ['Macast.py']
DATA_FILES = []
exec(open('macast/__pkginfo__.py').read())
copyright = 'Copyright {} xfangfang and the Macast contributors.'.format(datetime.datetime.now().year)
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.12.0',
        'CFBundleIdentifier': 'cn.xfangfang.Macast',
        'NSHumanReadableCopyright': copyright,
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
    },
    'excludes': ['PIL', 'tkinter'],
    'packages': ['rumps', 'macast', 'macast_renderer'],
    'iconfile': os.path.abspath('macast/assets/icon.icns')
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    py_modules=[]
)
