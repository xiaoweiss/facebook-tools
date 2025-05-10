#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门用于使用内置默认配置进行实际请求的修复脚本
本脚本会禁用模拟认证模式，强制使用内置默认配置进行实际请求
"""

import os
import sys
import shutil
import platform
import time

def main():
    """主函数"""
    print("🔧 禁用模拟认证，启用内置默认配置...")
    
    # 备份curl_helper.py
    if os.path.exists("curl_helper.py"):
        backup = f"curl_helper.py.bak.{int(time.time())}"
        shutil.copy2("curl_helper.py", backup)
        print(f"已备份 curl_helper.py -> {backup}")
    else:
        print("错误: 找不到curl_helper.py文件")
        return
    
    # 读取文件内容
    with open("curl_helper.py", "r") as f:
        content = f.read()
    
    # 修改模式设置
    if "MOCK_AUTH = True" in content:
        content = content.replace("MOCK_AUTH = True", "MOCK_AUTH = False")
    
    # 修改配置加载方式
    if "self._load_config()" in content:
        content = content.replace("self._load_config()", "# 直接使用内置默认配置\n        self._use_default_config()")
    
    # 添加实际请求调试输出
    if "print(f\"认证请求URL: {url}\")" in content and "print(f\"认证参数: username={username}\")" not in content:
        content = content.replace(
            "print(f\"认证请求URL: {url}\")", 
            "print(f\"认证请求URL: {url}\")\n            print(f\"认证参数: username={username}\")"
        )
    
    # 添加结果调试输出
    if "return response.json()" in content:
        content = content.replace(
            "return response.json()", 
            "result = response.json()\n            print(f\"解析JSON结果: {str(result)[:200]}...\")\n            return result"
        )
    
    # 修改加载提示
    if "print(\"已加载内置默认配置\")" in content:
        content = content.replace(
            "print(\"已加载内置默认配置\")", 
            "print(\"直接使用内置默认配置，不尝试加载外部配置\")"
        )
    
    # 简化_load_config方法
    if "def _load_config" in content:
        # 查找方法开始和结束位置
        start_index = content.find("def _load_config")
        if start_index != -1:
            next_def = content.find("def ", start_index + 10)
            if next_def != -1:
                # 替换整个方法
                old_method = content[start_index:next_def]
                new_method = """def _load_config(self, config_file='curl_config.json'):
        \"\"\"此方法现在不会被调用\"\"\"
        # 直接使用内置默认配置
        self._use_default_config()
        return

    """
                content = content.replace(old_method, new_method)
    
    # 保存修改后的文件
    with open("curl_helper.py", "w") as f:
        f.write(content)
    
    print("✅ 已修改curl_helper.py，现在将使用内置默认配置进行实际请求")
    print("✅ 已禁用模拟认证模式")
    
    # 创建新的curl_config.json文件（作为备份，虽然不会被使用）
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
    
    # 寻找json模块
    try:
        import json
        with open("curl_config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        print("✅ 已创建curl_config.json作为备份（虽然不会被使用）")
    except ImportError:
        print("注意: 无法创建curl_config.json备份文件")
    
    print("\n请尝试重新构建应用或运行现有应用。")

if __name__ == "__main__":
    main() 