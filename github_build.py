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

def main():
    # 获取系统信息
    system = platform.system()
    print(f"🖥️ 当前系统: {system}")
    
    # 确保已安装依赖
    print("📦 安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # 更新文件权限
    print("🔒 更新文件权限...")
    os.chmod("main.gui", 0o755)
    
    # 创建app_config.json文件以避免首次运行错误
    if not os.path.exists("app_config.json"):
        with open("app_config.json", "w") as f:
            f.write("{}")
        print("✅ 已创建默认配置文件")
    
    # 检查图标文件
    if system == "Windows":
        if not os.path.exists("app_icon.ico"):
            print("⚠️ 图标文件不存在，创建空图标...")
            shutil.copy("README.md", "app_icon.ico")  # 简单替代
    
    # 使用PyInstaller进行构建
    print("🚀 开始构建...")
    build_command = [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"]
    result = subprocess.run(build_command, check=False)
    
    if result.returncode != 0:
        print("❌ 构建失败，尝试诊断问题...")
        # 尝试显示更多调试信息
        subprocess.run([sys.executable, "-m", "pip", "list"], check=False)
        sys.exit(1)
    
    # 构建成功，后处理
    print("✅ 构建成功！")
    
    # 根据平台确定应用程序路径
    if system == "Windows":
        dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool.exe")
    else:
        dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool")
    
    # 打印最终应用程序路径
    if os.path.exists(dist_path):
        print(f"📂 应用程序已生成: {dist_path}")
        
        # 复制额外需要的配置文件
        if os.path.exists("curl_config.json"):
            output_dir = os.path.dirname(dist_path)
            shutil.copy("curl_config.json", output_dir)
            print("✅ 已复制配置文件到应用程序目录")
    else:
        print(f"⚠️ 无法找到生成的应用程序: {dist_path}")
        print("检查dist目录内容:")
        if os.path.exists("dist"):
            print(os.listdir("dist"))
    
    print("\n🎉 构建完成！")

if __name__ == "__main__":
    main() 