# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for InteractiveCatalog (.exe on Windows).
#
# Build (Windows):  pyinstaller --noconfirm --clean interactive_catalog.spec
# Output:           dist/InteractiveCatalog/InteractiveCatalog.exe
#
# PySide6 is collected by PyInstaller's own hook (Qt plugins included).
# pymupdf/PIL/reportlab are force-collected to be safe across versions.

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for package in ("pymupdf", "PIL", "reportlab"):
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += ["pymupdf", "fitz"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "matplotlib",
        "scipy",
        "numpy",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InteractiveCatalog",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
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
    name="InteractiveCatalog",
)