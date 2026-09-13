# -*- mode: python ; coding: utf-8 -*-
#
# One-file PyInstaller spec for InteractiveCatalog (single .exe on Windows).
#
# Build (Windows):  pyinstaller --noconfirm --clean interactive_catalog_onefile.spec
# Output:           dist/InteractiveCatalog.exe
#
# NOTE: one-file builds unpack to a temp folder at every launch, which
# antivirus engines flag more often than the onedir build. No UPX here.

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
    a.binaries,
    a.datas,
    [],
    name="InteractiveCatalog",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version="version_info.txt",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)