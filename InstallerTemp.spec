# -*- mode: python ; coding: utf-8 -*-


import os

datas_list = [('Assets', 'Assets'), ('icons', 'icons'), ('Agents', 'Agents')]
if os.path.exists('credentials.json'):
    datas_list.append(('credentials.json', '.'))
if os.path.exists('commit.txt'):
    datas_list.append(('commit.txt', '.'))

a = Analysis(
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'game_switcher', 'actions_context', 'actions_settings', 'ui_components', 'updater', 'win32com.client', 'requests',
        'googleapiclient', 'google_auth_oauthlib', 'google.auth.transport.requests', 'jsonschema',
        'google_auth_oauthlib.flow', 'googleapiclient.discovery', 'googleapiclient.http', 'google.oauth2.credentials',
        'wsgiref', 'wsgiref.simple_server'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'tcl', 'tk',
        'matplotlib', 'scipy', 'pandas', 'numpy',
        'doctest', 'pydoc', 'pdb',
        'PyQt5.QtNetwork', 'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtMultimedia',
        'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtSql',
        'PyQt5.QtTest', 'PyQt5.QtDesigner', 'PyQt5.QtXml', 'PyQt5.QtOpenGL',
        'PyQt5.Qt3D', 'PySide2', 'PySide6', 'wx'
    ],
    noarchive=False,
    optimize=2,
)
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
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.png'],
)