"""
HTTP请求工具核心功能
功能：
1. 获取认证令牌
2. 上报消费数据
"""

import json
import os
import requests

class APIClient:
    def __init__(self):
        self.config = {}
        self.session = requests.Session()
        self._load_config()

    def _load_config(self, config_file='curl_config.json'):
        """加载配置文件"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"配置加载失败: {str(e)}")

    def _build_url(self, endpoint):
        """构建完整URL"""
        base = self.config.get('base_url', '').rstrip('/')
        return f"{base}/{endpoint.lstrip('/')}"

    def get_auth_token(self, username, password):
        """获取认证令牌"""
        endpoint = self.config.get('endpoints', {}).get('get_auth', 'getAuth')
        try:
            response = self.session.get(
                url=self._build_url(endpoint),
                params={
                    "username": username,
                    "password": password,
                    "keep": 1,
                    "source": 3
                },
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"认证失败: {str(e)}")
            return None

    def report_spend(self, data):
        """上报消费数据"""
        endpoint = self.config.get('endpoints', {}).get('report_spend', 'index')
        try:
            response = self.session.post(
                url=self._build_url(endpoint),
                json=data,
                headers=self.config.get('default_headers', {}),
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"上报失败: {str(e)}")
            return None 