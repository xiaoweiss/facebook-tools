#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复已打包应用的配置文件问题
此脚本会将配置文件复制到正确位置并修复格式
"""

import os
import sys
import shutil
import json
import platform
import glob

def main():
    """主函数"""
    print("🔧 开始修复打包后的应用...")
    
    # 检测系统类型
    system = platform.system()
    print(f"检测到系统类型: {system}")
    
    # 查找dist目录
    dist_dir = find_dist_directory()
    if not dist_dir:
        print("❌ 无法找到dist目录，请确保已构建应用")
        return
    
    print(f"📂 找到dist目录: {dist_dir}")
    
    # 查找应用文件
    app_path = find_app_in_dist(dist_dir, system)
    if not app_path:
        print("❌ 无法在dist目录中找到应用文件")
        return
    
    print(f"🚀 找到应用: {app_path}")
    
    # 创建和复制配置文件
    fix_config_files(dist_dir, app_path, system)
    
    print("✅ 修复完成！请重新尝试运行应用")

def find_dist_directory():
    """查找dist目录"""
    # 首先检查当前目录下是否有dist
    if os.path.isdir("dist"):
        return os.path.abspath("dist")
    
    # 向上查找一层
    parent_dir = os.path.dirname(os.getcwd())
    parent_dist = os.path.join(parent_dir, "dist")
    if os.path.isdir(parent_dist):
        return parent_dist
    
    # 在当前目录下查找
    for item in os.listdir("."):
        if os.path.isdir(item) and "dist" in item.lower():
            return os.path.abspath(item)
    
    return None

def find_app_in_dist(dist_dir, system):
    """根据系统类型查找应用文件"""
    if system == "Windows":
        # 在Windows上查找.exe文件
        exe_files = glob.glob(os.path.join(dist_dir, "*.exe"))
        if exe_files:
            return exe_files[0]
    elif system == "Darwin":
        # 在macOS上查找应用
        app_files = glob.glob(os.path.join(dist_dir, "*"))
        for file in app_files:
            if os.path.isfile(file) and not file.endswith(".zip"):
                return file
    else:
        # 在Linux上查找可执行文件
        for file in os.listdir(dist_dir):
            file_path = os.path.join(dist_dir, file)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path
    
    return None

def fix_config_files(dist_dir, app_path, system):
    """修复配置文件"""
    # 准备配置内容
    config_data = {
        "base_url": "http://192.168.1.34:8082",
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
    
    # 创建配置文件
    config_path = os.path.join(dist_dir, "curl_config.json")
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)
    
    print(f"📝 已创建配置文件: {config_path}")
    
    # 对于macOS，可能需要复制到特殊位置
    if system == "Darwin" and os.path.isdir(app_path):
        app_contents = os.path.join(app_path, "Contents")
        if os.path.exists(app_contents):
            macos_paths = [
                os.path.join(app_contents, "MacOS"),
                os.path.join(app_contents, "Resources"),
                app_contents
            ]
            
            for path in macos_paths:
                if os.path.exists(path):
                    target_path = os.path.join(path, "curl_config.json")
                    shutil.copy(config_path, target_path)
                    print(f"📝 已复制配置文件到: {target_path}")
    
    # 创建app_config.json
    app_config_path = os.path.join(dist_dir, "app_config.json")
    with open(app_config_path, "w") as f:
        json.dump({}, f)
    
    print(f"📝 已创建app_config.json: {app_config_path}")
    
    # 创建一个简单的批处理文件/脚本来运行应用（带调试模式）
    if system == "Windows":
        bat_path = os.path.join(dist_dir, "run_debug.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\necho 启动调试模式...\n"{os.path.basename(app_path)}" --debug-auth\npause')
        print(f"📝 已创建调试启动脚本: {bat_path}")
    else:
        sh_path = os.path.join(dist_dir, "run_debug.sh")
        with open(sh_path, "w") as f:
            f.write(f'#!/bin/bash\necho "启动调试模式..."\n"{os.path.basename(app_path)}" --debug-auth')
        os.chmod(sh_path, 0o755)
        print(f"📝 已创建调试启动脚本: {sh_path}")

if __name__ == "__main__":
    main() 