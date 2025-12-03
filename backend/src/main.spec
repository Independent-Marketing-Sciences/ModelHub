# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get the site-packages directory dynamically
site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'

# Collect binary files (DLLs) for packages with native code
binaries = []

# XGBoost binaries - CRITICAL for xgboost to work
xgboost_lib_path = site_packages / 'xgboost' / 'lib'
if xgboost_lib_path.exists():
    for dll_file in xgboost_lib_path.glob('*.dll'):
        binaries.append((str(dll_file), 'xgboost/lib'))

# Collect other package binaries (numpy, scipy, sklearn often have DLLs)
for pkg_name in ['numpy', 'scipy', 'sklearn']:
    pkg_path = site_packages / pkg_name
    if pkg_path.exists():
        for dll_file in pkg_path.rglob('*.pyd'):
            rel_path = dll_file.relative_to(site_packages)
            binaries.append((str(dll_file), str(rel_path.parent)))

# Collect data files separately
datas = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
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

# Collect all data files for packages that need data files
# Only collect Python files and data, NOT binaries (those are handled separately above)
prophet_path = site_packages / 'prophet'
if prophet_path.exists():
    a.datas += Tree(str(prophet_path), prefix='prophet', excludes=['*.dll', '*.pyd', '*.so'])

statsmodels_path = site_packages / 'statsmodels'
if statsmodels_path.exists():
    a.datas += Tree(str(statsmodels_path), prefix='statsmodels', excludes=['*.dll', '*.pyd', '*.so'])

# Note: Removed setuptools Tree collection to avoid pkg_resources issues
# PyInstaller's hooks should handle this automatically

# XGBoost data files (Python code, but NOT the binaries - those are in binaries=[] above)
xgboost_path = site_packages / 'xgboost'
if xgboost_path.exists():
    a.datas += Tree(str(xgboost_path), prefix='xgboost', excludes=['*.dll', '*.pyd', '*.so'])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='modelling-mate-backend',
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