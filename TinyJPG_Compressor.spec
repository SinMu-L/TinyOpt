# -*- mode: python ; coding: utf-8 -*-

import datetime

# 获取当前日期，格式为 YYYYMMDD（例如 20260529）
current_date = datetime.datetime.now().strftime('%Y%m%d')

# 定义你的基础版本号
version = "v1.3.2"

# 拼接成最终的程序名称：TinyJPG_Compressor_v1.0.0_20260529
app_name = f"TinyJPG_Compressor_{version}_{current_date}"


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.png', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
