# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys

block_cipher = None

# 添加隐藏导入
hiddenimports = [
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'facebook_operations',
    'browser_utils',
    'websockets',
    'selenium.webdriver.remote',
    'schedule',
    'tzlocal',  # 新增时区支持
    'pytz',      # 时区支持
    'curl_helper', # API客户端
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.action_chains'
]

# 动态收集数据文件
datas, binaries, hiddenimports = collect_all('fb_billing_operations')

# 确保包含数据文件
datas.append(('curl_config.json', '.'))  # 配置文件

a = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FacebookAdManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # 临时启用控制台用于调试
    icon='app_icon.ico',  # 准备一个ICO文件
    disable_windowed_traceback=False,
    onefile=True,  # 关键参数：生成单个文件
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 添加Windows图标支持
if sys.platform == 'win32':
    exe.icon = 'app_icon.ico'
else:
    exe.icon = None 