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
    'selenium.webdriver.common.action_chains',
    'adspower_detector',  # 新增自动检测模块
    'tkinter.filedialog',  # 确保文件对话框支持
    'win32api',  # 添加Windows API支持
    'win32con',
    'queue',  # 添加队列支持
    'traceback',  # 添加异常追踪
    'fb_billing_operations',  # 确保包含业务逻辑模块
    'requests',  # 确保包含requests库
    'urllib3',   # requests的依赖
    'requests.adapters',
    'urllib3.util.retry',
]

# 动态收集数据文件
datas, binaries, hiddenimports = collect_all('fb_billing_operations')

# 确保包含数据文件
datas.append(('curl_config.json', '.'))  # 配置文件

a = Analysis(
    ['main_gui.py', 'components/path_selector.py', 'fb_billing_operations.py', 'core/__init__.py'],
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
    console=False,   # 正式发布时关闭
    icon='app_icon.ico',  # 准备一个ICO文件
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 在Analysis后添加打包模式配置
if sys.platform == 'win32':
    exe.onefile = True
else:
    exe.onefile = False

# 添加Windows图标支持
if sys.platform == 'win32':
    exe.icon = 'app_icon.ico'
else:
    exe.icon = None 