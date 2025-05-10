# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 添加隐藏导入
hiddenimports = [
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
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
    'queue',  # 添加队列支持
    'traceback',  # 添加异常追踪
    'fb_billing_operations',  # 确保包含业务逻辑模块
    'requests',  # 确保包含requests库
    'urllib3',   # requests的依赖
    'requests.adapters',
    'urllib3.util.retry',
    're',  # 正则表达式支持
    'apscheduler.schedulers',
    'apscheduler.jobstores',
    'apscheduler.executors',
    'apscheduler.events'
]

# 动态收集所有数据文件
datas = []
binaries = []

# 收集所有模块的数据文件
for module in ['fb_billing_operations', 'selenium', 'pytz']:
    try:
        module_datas, module_binaries, module_hiddenimports = collect_all(module)
        datas.extend(module_datas)
        binaries.extend(module_binaries)
        hiddenimports.extend(module_hiddenimports)
    except Exception as e:
        print(f"警告: 无法收集模块 {module} 的数据，错误信息: {str(e)}")

# 确保包含配置文件
try:
    if os.path.exists('curl_config.json'):
        datas.append(('curl_config.json', '.'))
except Exception as e:
    print(f"警告: 无法添加配置文件，错误信息: {str(e)}")

# 包含时区数据 - 使用更健壮的方式
import site
try:
    site_packages_list = site.getsitepackages()
    for site_package in site_packages_list:
        pytz_path = os.path.join(site_package, 'pytz', 'zoneinfo')
        if os.path.exists(pytz_path):
            datas.append((pytz_path, 'pytz/zoneinfo'))
            print(f"找到pytz时区数据: {pytz_path}")
            break
    else:
        print("警告: 无法找到pytz时区数据")
except Exception as e:
    print(f"警告: 获取pytz路径异常: {str(e)}")

# 添加主程序文件
added_files = [
    ('main.gui', '.'),
]

# 统一图标文件名
icon_file = 'app_icon.ico'

# 如果是Windows系统，添加图标
if sys.platform == 'win32':
    try:
        if os.path.exists(icon_file):
            added_files.append((icon_file, '.'))
        else:
            print(f"警告: 图标文件 {icon_file} 不存在")
    except Exception as e:
        print(f"警告: 添加图标异常: {str(e)}")

# 添加app_config.json
try:
    if not os.path.exists('app_config.json'):
        with open('app_config.json', 'w') as f:
            f.write('{}')
        print("已创建默认app_config.json")
    datas.append(('app_config.json', '.'))
except Exception as e:
    print(f"警告: 无法处理app_config.json，错误信息: {str(e)}")

a = Analysis(
    ['main.gui'],
    pathex=[],
    binaries=binaries,
    datas=datas + added_files,
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
    name='FbAutoTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 改为True以便在CI环境中查看输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if sys.platform == 'win32' and os.path.exists(icon_file) else None,
)

# 设置打包模式
exe.onefile = True

# 添加Windows图标支持
if sys.platform == 'win32':
    try:
        if os.path.exists(icon_file):
            exe.icon = icon_file
        else:
            exe.icon = None
    except Exception as e:
        print(f"警告: 设置图标异常: {str(e)}")
        exe.icon = None
else:
    exe.icon = None 