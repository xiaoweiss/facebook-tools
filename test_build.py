#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试构建脚本
用于验证认证URL修复是否有效
"""

import os
import subprocess
import sys
import platform
import shutil
import json
import time

def main():
    # 获取系统信息
    system = platform.system()
    print(f"🖥️ 当前系统: {system}")
    
    # 备份原始配置文件
    backup_config_files()
    
    try:
        # 创建并验证配置文件
        print("🔧 创建测试配置文件...")
        create_test_config()
        
        # 确保已安装依赖
        print("📦 安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # 更新文件权限
        print("🔒 更新文件权限...")
        if system != "Windows":
            os.chmod("main.gui", 0o755)
        
        # 使用PyInstaller进行构建
        print("🚀 开始构建测试版本...")
        if system == "Windows":
            build_command = [sys.executable, "-m", "PyInstaller", "main.gui", "--onefile", "--clean"]
        else:
            build_command = [sys.executable, "-m", "PyInstaller", "main.gui", "--onefile", "--clean"]
            
        result = subprocess.run(build_command, check=False)
        
        if result.returncode != 0:
            print("❌ 构建失败，请检查错误信息")
            return
        
        # 构建成功，复制配置文件
        print("✅ 构建成功！")
        
        # 确定dist目录和应用路径
        dist_dir = os.path.join(os.getcwd(), "dist")
        if system == "Windows":
            app_path = os.path.join(dist_dir, "main.exe")
        else:
            app_path = os.path.join(dist_dir, "main")
        
        # 复制测试配置到dist目录
        if os.path.exists("test_curl_config.json"):
            shutil.copy("test_curl_config.json", os.path.join(dist_dir, "curl_config.json"))
            print(f"✅ 已复制测试配置到: {dist_dir}")
        
        # 尝试运行应用
        if os.path.exists(app_path):
            print(f"🚀 正在测试运行应用: {app_path}")
            print("请输入测试授权账号并检查URL是否正确构建...")
            
            # 在另一个终端窗口启动应用
            if system == "Windows":
                subprocess.Popen(f"start {app_path}", shell=True)
            else:
                subprocess.Popen(['open', app_path])
        else:
            print(f"⚠️ 无法找到构建的应用: {app_path}")
    
    finally:
        # 恢复原始配置文件
        restore_config_files()
        print("✅ 已恢复原始配置文件")

def create_test_config():
    """创建用于测试的配置文件"""
    test_config = {
        "base_url": "http://httpbin.org",
        "default_headers": {
            "Content-Type": "application/json",
            "X-Client": "TestClient/1.0"
        },
        "timeout": 10,
        "endpoints": {
            "get_auth": "get",
            "report_spend": "post"
        }
    }
    
    with open("test_curl_config.json", "w") as f:
        json.dump(test_config, f, indent=2)
    
    # 同时修改curl_helper.py中的请求处理
    if os.path.exists("curl_helper.py"):
        with open("curl_helper.py", "r") as f:
            content = f.read()
        
        # 添加测试模式
        if "DEBUG_MODE = False" not in content:
            test_content = content.replace(
                "class APIClient:",
                "DEBUG_MODE = True\n\nclass APIClient:"
            )
            
            # 修改get_auth_token方法返回测试数据
            if DEBUG_MODE:
                test_content = test_content.replace(
                    "return response.json()",
                    "if DEBUG_MODE and response.status_code == 200:\n                return {'code': 1, 'msg': 'Test Auth Success'}\n            return response.json()"
                )
            
            with open("curl_helper_test.py", "w") as f:
                f.write(test_content)
            
            # 创建备份并替换
            shutil.copy("curl_helper.py", "curl_helper.bak")
            shutil.copy("curl_helper_test.py", "curl_helper.py")

def backup_config_files():
    """备份原始配置文件"""
    files_to_backup = ["curl_config.json", "app_config.json", "curl_helper.py"]
    for file in files_to_backup:
        if os.path.exists(file):
            backup_file = f"{file}.bak"
            shutil.copy(file, backup_file)
            print(f"已备份 {file} -> {backup_file}")

def restore_config_files():
    """恢复原始配置文件"""
    files_to_restore = ["curl_config.json", "app_config.json", "curl_helper.py"]
    for file in files_to_restore:
        backup_file = f"{file}.bak"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, file)
            os.remove(backup_file)
            print(f"已恢复 {file}")

if __name__ == "__main__":
    main() 