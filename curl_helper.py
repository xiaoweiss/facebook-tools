"""
HTTP请求工具核心功能
功能：
1. 获取认证令牌
2. 上报消费数据
"""

import json
import os
import sys
import requests
import urllib.parse

# 关闭模拟认证模式，使用内置默认配置进行实际请求
MOCK_AUTH = False

class APIClient:
    def __init__(self):
        self.config = {}
        self.session = requests.Session()
        # 直接使用内置默认配置，不尝试加载外部配置文件
        self._use_default_config()

    def _load_config(self, config_file='curl_config.json'):
        """此方法现在不会被调用"""
        # 直接使用内置默认配置
        self._use_default_config()
        return

    def _use_default_config(self):
        """使用内置默认配置"""
        self.config = {
            "base_url": "http://192.168.1.34:8082/",
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
        print("直接使用内置默认配置，不尝试加载外部配置")
        # 检查并修复base_url
        if 'base_url' in self.config:
            self.config['base_url'] = self._normalize_base_url(self.config['base_url'])

    def _normalize_base_url(self, url):
        """标准化处理base_url"""
        if not url:
            print("警告: base_url为空")
            return "http://192.168.1.34:8082/"
            
        # 确保URL有协议前缀
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}' if any(local in url for local in ['localhost', '192.168', '127.0.0.1']) else f'https://{url}'
        
        # 确保URL以/结尾
        if not url.endswith('/'):
            url += '/'
            
        return url

    def _build_url(self, endpoint):
        """构建完整API URL"""
        base = self.config.get('base_url', '')
        if not base:
            print("错误: base_url未配置")
            # 使用默认值而不是返回空字符串
            base = "http://192.168.1.34:8082/"
            
        # 去除endpoint开头的斜杠
        endpoint = endpoint.lstrip('/')
        
        # 使用urllib.parse确保URL正确拼接
        full_url = urllib.parse.urljoin(base, endpoint)
        
        print(f"调试: 构建URL: {full_url}")
        return full_url

    def get_auth_token(self, username):
        """获取认证令牌"""
        # 模拟认证模式，直接返回成功
        if MOCK_AUTH:
            print("模拟认证模式: 返回模拟成功结果")
            return {"code": 1, "msg": "模拟授权成功", "time": 1746871000, "data": {"token": "mock_token_123456789"}}
        
        endpoint = self.config.get('endpoints', {}).get('get_auth', 'index.php/api/finance.Callback/getAuth')
        try:
            url = self._build_url(endpoint)
            if not url:
                raise ValueError("无法构建有效的认证URL")
                
            print(f"认证请求URL: {url}")
            print(f"认证参数: username={username}")
            response = self.session.get(
                url=url,
                params={
                    "username": username,
                },
                timeout=self.config.get('timeout', 30)
            )
            print(f"认证响应状态码: {response.status_code}")
            
            # 尝试打印响应内容
            try:
                print(f"认证响应内容: {response.text[:200]}...")  # 只打印前200个字符
            except Exception as e:
                print(f"无法打印响应内容: {str(e)}")
                
            response.raise_for_status()
            result = response.json()
            print(f"解析JSON结果: {str(result)[:200]}...")
            return result
        except Exception as e:
            print(f"认证失败: {str(e)}")
            # 特殊情况下模拟成功响应，仅用于调试
            if "--debug-auth" in sys.argv:
                print("调试模式: 返回模拟的成功响应")
                return {"code": 1, "msg": "Debug Auth Success"}
            return None

    def report_spend(self, data):
        """上报消费数据"""
        endpoint = self.config.get('endpoints', {}).get('report_spend', 'index.php/api/finance.Callback/index')
        try:
            url = self._build_url(endpoint)
            if not url:
                raise ValueError("无法构建有效的上报URL")
                
            print(f"上报请求URL: {url}")
            response = self.session.post(
                url=url,
                json=data,
                headers=self.config.get('default_headers', {}),
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"上报失败: {str(e)}")
            return None 