# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ble_scanner.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['sqlalchemy','aiosqlite','services', 'database', 'scanners','bleak'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ble_scanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    strip=True,
    upx=True,
    upx_exclude=[],
    name='ble_scanner',
)
app = BUNDLE(
    coll,
    name='ble_scanner.app',
    icon=None,
    bundle_identifier=None,
)