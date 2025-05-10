#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows专用构建脚本
用于在Windows环境中构建应用程序
"""

import os
import subprocess
import sys
import platform
import shutil

def main():
    # 检查系统类型
    if platform.system() != 'Windows':
        print("⚠️ 这个脚本仅支持在Windows上运行")
        sys.exit(1)
    
    # 确保已安装依赖
    print("📦 安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # 确保有icon文件
    if not os.path.exists("app_icon.ico"):
        print("⚠️ 缺少图标文件app_icon.ico，将使用默认图标")
    
    # 确保存在配置文件
    if not os.path.exists("app_config.json"):
        with open("app_config.json", "w") as f:
            f.write("{}")
        print("✅ 已创建默认配置文件")
    
    # 使用PyInstaller进行构建
    print("🚀 开始构建...")
    build_command = [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"]
    result = subprocess.run(build_command, check=False)
    
    if result.returncode != 0:
        print("❌ 构建失败，请检查错误信息")
        sys.exit(1)
    
    # 构建成功，后处理
    print("✅ 构建成功！")
    dist_path = os.path.join(os.getcwd(), "dist", "FbAutoTool.exe")
    
    # 打印最终应用程序路径
    if os.path.exists(dist_path):
        print(f"📂 应用程序已生成: {dist_path}")
        
        # 复制额外需要的配置文件
        output_dir = os.path.dirname(dist_path)
        if os.path.exists("curl_config.json"):
            shutil.copy("curl_config.json", output_dir)
            print("✅ 已复制配置文件到应用程序目录")
    else:
        print("⚠️ 无法找到生成的应用程序")
    
    print("\n🎉 构建完成！")
    print("您可以通过双击以下文件运行应用:")
    print(f"  {dist_path}")

if __name__ == "__main__":
    main() 