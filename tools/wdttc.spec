# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all Playwright submodules
playwright_submodules = collect_submodules('playwright')

# Collect all Playwright data files
playwright_datas = collect_data_files('playwright')

a = Analysis(
    ['..\\src\\wdttc.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\plugins', 'plugins')],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'playwright.async_api',
        *playwright_submodules,  # Add all Playwright submodules
        'requests',
        'openpyxl'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='wdttc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='wdttc',
)
