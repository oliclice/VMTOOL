# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['vmtool.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'numpy', 'scipy', 'pandas', 'numba', 'llvmlite', 'pyarrow', 'lxml', 'rapidfuzz', 'openpyxl', 'xlrd', 'xlwt', 'botocore', 'boto3', 's3transfer', 'awscli', 'psycopg', 'psycopg2', 'psycopg_binary', 'mysqlclient', 'pymysql', 'django', 'flask', 'fastapi', 'uvicorn', 'starlette', 'matplotlib', 'seaborn', 'plotly', 'bokeh', 'PIL', 'pillow', 'opencv', 'IPython', 'ipykernel', 'ipywidgets', 'nbformat', 'nbconvert', 'jupyter', 'pytest', 'hypothesis', 'black', 'isort', 'ruff', 'mypy', 'torch', 'torchvision', 'torchaudio', 'tensorflow', 'keras', 'zmq', 'celery', 'redis', 'kafka', 'jedi', 'parso', 'tkinter', '_tkinter', 'setuptools', 'pkg_resources', 'wheel', 'pip', 'cryptography', 'paramiko', 'bcrypt', 'aiohttp', 'httpx', 'requests', 'jsonschema', 'pydantic_extra_types'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vmtool-gui',
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vmtool-gui',
)
