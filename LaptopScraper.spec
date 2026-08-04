# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scrape_and_compile.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'acer_scraper',
        'allit_scraper',
        'asus_scraper',
        'lenovo_scraper',
        'msi_scraper',
        'pcimage_scraper',
        'techhypermart_scraper',
        'cloudscraper',
        'curl_cffi',
        'bs4',
        'lxml',
        'requests',
        'selenium'
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
    a.binaries,
    a.datas,
    [],
    name='LaptopScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
