import os
import sys
from pathlib import Path
import winreg  # Windows注册表操作
from ctypes import windll  # 获取逻辑磁盘

def find_adspower():
    """智能定位AdsPower安装路径（毫秒级响应）"""
    try:
        print("🕵️ 开始定位AdsPower...")
        # 1. 检查正在运行的进程路径（最快）
        if path := _get_running_process_path():
            print(f"✅ 通过进程定位到路径: {path}")
            return path

        # 2. 注册表精准查询（专业版安装）
        if path := _check_install_registry():
            return path

        # 3. 检查桌面快捷方式（用户常用入口）
        if path := _parse_shortcut():
            return path

        # 4. 环境变量指定路径（最高优先级）
        if 'ADSPOWER_PATH' in os.environ:
            return os.environ['ADSPOWER_PATH']

        # 5. 系统命令快速定位（where命令）
        if path := _find_via_cmd():
            return path

    except Exception as e:
        print(f"定位异常: {str(e)}")

    # 6. 最后才尝试全盘扫描（按概率排序路径）
    return _smart_disk_scan()

def _get_running_process_path():
    """通过任务管理器获取正在运行的进程路径"""
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'exe']):
            if proc.info['name'] == 'ads.exe':
                return os.path.dirname(proc.info['exe'])
    except ImportError:
        # 回退到wmic命令
        result = os.popen('wmic process where "name=\'ads.exe\'" get ExecutablePath').read()
        if paths := [line.strip() for line in result.splitlines() if line.strip()]:
            return os.path.dirname(paths[0])
    return None

def _check_install_registry():
    """查询多个可能的注册表项"""
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AdsPower",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\AdsPower",
        r"SOFTWARE\Clients\StartMenuInternet\AdsPower"
    ]
    
    for path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                return winreg.QueryValueEx(key, "InstallLocation")[0]
        except FileNotFoundError:
            continue
    return None

def _parse_shortcut():
    """解析桌面快捷方式"""
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    for file in os.listdir(desktop):
        if file.endswith('.lnk') and 'adspower' in file.lower():
            try:
                from win32com.client import Dispatch
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(os.path.join(desktop, file))
                return os.path.dirname(shortcut.TargetPath)
            except ImportError:
                break
    return None

def _find_via_cmd():
    """使用where命令快速定位"""
    result = os.popen('where /r C:\\ ads.exe 2>nul').read().strip()
    if result and os.path.exists(result):
        return os.path.dirname(result)
    return None

def _smart_disk_scan():
    """智能磁盘扫描（优先用户常用目录）"""
    priority_paths = [
        os.path.expandvars(r"%ProgramFiles%"),
        os.path.expandvars(r"%USERPROFILE%\Downloads"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs")
    ]
    
    for path in priority_paths:
        for root, dirs, files in os.walk(path):
            if 'ads.exe' in files:
                return root
            # 深度限制（最多3层目录）
            if root.count(os.sep) - path.count(os.sep) > 3:
                del dirs[:]
    return None 