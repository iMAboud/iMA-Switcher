# -*- mode: python ; coding: utf-8 -*-


import os

# Ensure UPX is found if installed via WinGet
upx_dir = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links')
if os.path.isdir(upx_dir) and upx_dir not in os.environ.get('PATH', ''):
    os.environ['PATH'] = upx_dir + os.pathsep + os.environ.get('PATH', '')

datas_list = [('Assets', 'Assets')]
if os.path.exists('credentials.json'):
    datas_list.append(('credentials.json', '.'))
if os.path.exists('commit.txt'):
    datas_list.append(('commit.txt', '.'))
if os.path.exists('CHANGELOG.md'):
    datas_list.append(('CHANGELOG.md', '.'))

a = Analysis(
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'game_switcher', 'actions_context', 'actions_settings', 'ui_components', 'theme_manager', 'updater',
        'googleapiclient', 'google_auth_oauthlib', 'google.auth.transport.requests',
        'google_auth_oauthlib.flow', 'googleapiclient.discovery', 'googleapiclient.http', 'google.oauth2.credentials',
        'wsgiref', 'wsgiref.simple_server'
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'tcl', 'tk',
        'matplotlib', 'scipy', 'pandas', 'numpy',
        'doctest', 'pydoc', 'pdb',
        'PIL', 'Pillow', 'psutil', 'jsonschema',
        'win32com', 'pywintypes', 'win32api',
        'PyQt5.QtNetwork', 'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtMultimedia',
        'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtSql',
        'PyQt5.QtTest', 'PyQt5.QtDesigner', 'PyQt5.QtXml', 'PyQt5.QtOpenGL',
        'PyQt5.Qt3D', 'PyQt5.QtSvg', 'PySide2', 'PySide6', 'wx',
        'setuptools', 'pkg_resources', 'packaging',
        'multiprocessing', '_lzma', '_bz2',
        'unittest', 'jinja2', 'markupsafe', 'asyncio', '_asyncio',
        '_overlapped', '_wmi', '_decimal', 'decimal', 'webbrowser',
        'pyparsing.diagram', 'curses', 'pydoc_data', 'test', 'tests',
        'difflib', 'ftplib', 'imaplib', 'poplib', 'smtplib', 'telnetlib', 'xmlrpc'
    ],
    noarchive=False,
    optimize=2,
)

# Deduplicate and filter a.datas (removes duplicate bundles, runtime cache, translations)
seen_datas = set()
filtered_datas = []
for item in a.datas:
    dest_norm = item[0].replace('/', '\\').lower()
    if dest_norm in seen_datas:
        continue
    if dest_norm.startswith('assets\\cache'):
        continue
    if dest_norm.endswith('.qm'):
        continue
    seen_datas.add(dest_norm)
    filtered_datas.append(item)
a.datas = filtered_datas

# Filter unused Qt DLLs and plugins from a.binaries
qt_exclude = {
    'opengl32sw.dll', 'd3dcompiler_47.dll',
    'qt5quick.dll', 'qt5qml.dll', 'qt5qmlmodels.dll',
    'qt5network.dll', 'qt5dbus.dll', 'qt5websockets.dll',
    'libglesv2.dll', 'libegl.dll',
    'qt5svg.dll',
    'qminimal.dll', 'qoffscreen.dll', 'qwebgl.dll',
    'qtiff.dll', 'qicns.dll', 'qtga.dll', 'qwbmp.dll',
    'qsvgicon.dll', 'qsvg.dll',
    'qxdgdesktopportal.dll', 'qtuiotouchplugin.dll',
}
a.binaries = [b for b in a.binaries if os.path.basename(b[0]).lower() not in qt_exclude]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='iMA Switcher Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll'],
    runtime_tmpdir=None,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Assets/logo.png'],
)