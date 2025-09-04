#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions专用构建脚本
适用于在GitHub Actions或其他CI环境中构建应用
"""

import os
import subprocess
import sys
import platform
import shutil
import json
import io
import locale

def main():
    # 修复Windows编码问题
    if platform.system() == "Windows":
        # 尝试设置控制台编码为UTF-8
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except:
            pass
    
    # 获取系统信息
    system = platform.system()
    print(f"当前系统: {system}")
    
    # 确保已安装依赖
    print("安装依赖...")
    try:
        # 根据系统选择合适的Python路径
        python_exe = sys.executable
        if system == "Windows" and os.environ.get("GITHUB_ACTIONS") == "true":
            # 在GitHub Actions的Windows环境中使用特定路径
            python_exe = r"C:\hostedtoolcache\windows\Python\3.10.11\x64\python.exe"
            if not os.path.exists(python_exe):
                print(f"警告: 指定的Python路径不存在: {python_exe}，使用默认路径")
                python_exe = sys.executable
        
        # 使用--user选项安装依赖，避免权限问题
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt", "--user"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"警告: 安装依赖失败: {e}")
        # 尝试不使用--user选项
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # 更新文件权限
    print("更新文件权限...")
    os.chmod("main.gui", 0o755)
    
    # 创建并验证配置文件
    print("检查配置文件...")
    ensure_config_files()
    
    # 检查图标文件
    if system == "Windows":
        if not os.path.exists("app_icon.ico"):
            print("警告: 图标文件不存在，创建空图标...")
            shutil.copy("README.md", "app_icon.ico")  # 简单替代
    
    # 使用PyInstaller进行构建
    print("开始构建...")
    python_exe = sys.executable
    if system == "Windows" and os.environ.get("GITHUB_ACTIONS") == "true":
        # 在GitHub Actions的Windows环境中使用特定路径
        python_exe = r"C:\hostedtoolcache\windows\Python\3.10.11\x64\python.exe"
        if not os.path.exists(python_exe):
            print(f"警告: 指定的Python路径不存在: {python_exe}，使用默认路径")
            python_exe = sys.executable
    
    build_command = [python_exe, "-m", "PyInstaller", "build.spec", "--clean"]
    result = subprocess.run(build_command, check=False)
    
    if result.returncode != 0:
        print("构建失败，尝试诊断问题...")
        # 尝试显示更多调试信息
        subprocess.run([python_exe, "-m", "pip", "list"], check=False)
        sys.exit(1)
    
    # 构建成功，后处理
    print("构建成功！")
    
    # 根据平台确定应用程序路径
    if system == "Windows":
        dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool.exe")
        dist_dir = os.path.join(os.getcwd(), "dist")
    else:
        dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool")
        dist_dir = os.path.join(os.getcwd(), "dist")
    
    # 打印最终应用程序路径
    if os.path.exists(dist_path):
        print(f"应用程序已生成: {dist_path}")
        
        # 复制额外需要的配置文件
        copy_config_files_to_dist(dist_dir)
    else:
        print(f"警告: 无法找到生成的应用程序: {dist_path}")
        print("检查dist目录内容:")
        if os.path.exists("dist"):
            print(os.listdir("dist"))
    
    print("\n构建完成！")

def ensure_config_files():
    """确保所有配置文件存在且格式正确"""
    # 检查app_config.json
    if not os.path.exists("app_config.json"):
        with open("app_config.json", "w") as f:
            json.dump({}, f, indent=2)
        print("已创建默认app_config.json文件")

    # 检查curl_config.json
    if not os.path.exists("curl_config.json"):
        default_config = {
            "base_url": "http://192.168.1.196:8082",
            "default_headers": {
                "Content-Type": "application/json",
                "X-Client": "FacebookAdsManager/1.0"
            },
            "timeout": 30,
            "endpoints": {
                "get_auth": "index.php/api/finance.Callback/getAuth",
                "report_spend": "index.php/api/finance.Callback/index"
            }
        }
        with open("curl_config.json", "w") as f:
            json.dump(default_config, f, indent=2)
        print("已创建默认curl_config.json文件")
    else:
        # 验证并修复现有的curl_config.json
        try:
            with open("curl_config.json", "r") as f:
                config = json.load(f)
            
            # 确保base_url格式正确
            if "base_url" in config:
                if config["base_url"].endswith("/"):
                    config["base_url"] = config["base_url"].rstrip("/")
                if not config["base_url"].startswith(("http://", "https://")):
                    config["base_url"] = "http://" + config["base_url"]
            
            # 修复endpoints路径
            if "endpoints" in config:
                for key, value in config["endpoints"].items():
                    if value.startswith("/"):
                        config["endpoints"][key] = value.lstrip("/")
            
            # 保存修复后的配置
            with open("curl_config.json", "w") as f:
                json.dump(config, f, indent=2)
            print("已验证并修复curl_config.json")
        except Exception as e:
            print(f"警告: curl_config.json验证失败: {str(e)}")

def copy_config_files_to_dist(dist_dir):
    """确保配置文件被复制到正确位置"""
    config_files = ["curl_config.json", "app_config.json"]
    for config_file in config_files:
        if os.path.exists(config_file):
            # 对于macOS，需要复制到应用目录下
            if platform.system() == "Darwin":
                app_path = os.path.join(dist_dir, "FbAutoTool")
                if os.path.isdir(app_path):  # 如果是目录（macOS应用包）
                    shutil.copy(config_file, app_path)
                else:
                    shutil.copy(config_file, dist_dir)
            else:
                shutil.copy(config_file, dist_dir)
            print(f"已复制 {config_file} 到应用程序目录")
        else:
            print(f"警告: 配置文件 {config_file} 不存在，无法复制")

if __name__ == "__main__":
    # 设置环境变量以确保UTF-8编码
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    main() 