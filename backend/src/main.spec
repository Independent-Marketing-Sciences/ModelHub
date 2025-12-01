# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get the site-packages directory dynamically
site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pandas',
        'numpy',
        'prophet',
        'prophet.serialize',
        'scipy',
        'scipy.special',
        'scipy.special._ufuncs_cxx',
        'sklearn',
        'sklearn.utils',
        'sklearn.utils._cython_blas',
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._partition_nodes',
        'sklearn.tree',
        'sklearn.tree._utils',
        'statsmodels',
        'statsmodels.tsa',
        'statsmodels.tsa.statespace',
        'statsmodels.tsa.statespace._filters',
        'statsmodels.tsa.statespace._smoothers',
        'xgboost',
        'plotly',
        'cmdstanpy',
        'stanio',
        'pydantic',
        'pydantic_core',
        'multipart',
        'starlette',
        'starlette.applications',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect all data files for these packages dynamically
prophet_path = site_packages / 'prophet'
if prophet_path.exists():
    a.datas += Tree(str(prophet_path), prefix='prophet')

statsmodels_path = site_packages / 'statsmodels'
if statsmodels_path.exists():
    a.datas += Tree(str(statsmodels_path), prefix='statsmodels')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
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