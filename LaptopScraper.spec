# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scrape_and_compile.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'scrapers.acer_scraper',
        'scrapers.allit_scraper',
        'scrapers.asus_scraper',
        'scrapers.lenovo_scraper',
        'scrapers.msi_scraper',
        'scrapers.pcimage_scraper',
        'scrapers.techhypermart_scraper',
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
