"""
HTTP请求工具核心功能
功能：
1. 获取认证令牌
2. 上报消费数据
"""

import json
import os
import requests
import urllib.parse

class APIClient:
    def __init__(self):
        self.config = {}
        self.session = requests.Session()
        self._load_config()

    def _load_config(self, config_file='curl_config.json'):
        """加载配置文件"""
        # 优先查找与可执行文件同目录下的配置
        exe_dir = os.path.dirname(os.path.abspath(__file__))
        local_config = os.path.join(exe_dir, config_file)
        
        if os.path.exists(local_config):
            config_path = local_config
        elif os.path.exists(config_file):
            config_path = config_file
        else:
            print(f"警告: 找不到配置文件 {config_file}")
            return
            
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            # 新增验证逻辑
            if not self.config.get('endpoints'):
                raise ValueError("endpoints配置缺失")
            if not isinstance(self.config['endpoints'], dict):
                raise TypeError("endpoints必须为字典类型")
            
            # 检查并修复base_url
            if 'base_url' in self.config:
                self.config['base_url'] = self._normalize_base_url(self.config['base_url'])
                
        except Exception as e:
            print(f"配置加载失败: {str(e)}")

    def _normalize_base_url(self, url):
        """标准化处理base_url"""
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
            return ""
            
        # 去除endpoint开头的斜杠
        endpoint = endpoint.lstrip('/')
        
        # 使用urllib.parse确保URL正确拼接
        full_url = urllib.parse.urljoin(base, endpoint)
        
        print(f"DEBUG: 构建URL: {full_url}")
        return full_url

    def get_auth_token(self, username):
        """获取认证令牌"""
        endpoint = self.config.get('endpoints', {}).get('get_auth', 'getAuth')
        try:
            url = self._build_url(endpoint)
            if not url:
                raise ValueError("无法构建有效的认证URL")
                
            print(f"认证请求URL: {url}")
            response = self.session.get(
                url=url,
                params={
                    "username": username,
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