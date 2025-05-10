#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS专用构建脚本
用于解决build.spec的跨平台问题，确保在macOS上能够正确构建
"""

import os
import subprocess
import sys
import platform

def main():
    # 确认系统类型
    if platform.system() != 'Darwin':
        print("⚠️ 这个脚本仅支持在macOS上运行")
        sys.exit(1)
    
    # 确保已安装依赖
    print("📦 安装依赖...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    
    # 更新文件权限
    print("🔒 更新文件权限...")
    subprocess.run(["chmod", "+x", "main.gui"], check=True)
    
    # 使用PyInstaller进行构建
    print("🚀 开始构建...")
    build_command = ["pyinstaller", "build.spec", "--clean"]
    result = subprocess.run(build_command, check=False)
    
    if result.returncode != 0:
        print("❌ 构建失败，检查是否有依赖问题")
        sys.exit(1)
    
    # 构建成功，后处理
    print("✅ 构建成功！")
    dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool")
    
    # 打印最终应用程序路径
    if os.path.exists(dist_path):
        print(f"📂 应用程序已生成: {dist_path}")
        # 复制额外需要的配置文件
        subprocess.run(["cp", "curl_config.json", dist_path], check=False)
        print("✅ 已复制配置文件到应用程序目录")
    else:
        print("⚠️ 无法找到生成的应用程序")
    
    print("\n🎉 构建完成！")
    print("🚀 使用以下命令运行应用:")
    print(f"$ {dist_path}")

if __name__ == "__main__":
    main() 