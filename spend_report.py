"""
广告数据上报模块
作者：DeepSeek-R1
最后更新：2024-06-20
"""

import requests
import json
from datetime import datetime

class ReportClient:
    def __init__(self, base_url="http://192.168.1.196:8082"):
        self.base_url = base_url
        self.token = None
        self.source = "facebook_ads_tool_v1.0"

    def _request(self, endpoint, method="POST", params=None, data=None):
        """统一请求方法"""
        url = f"{self.base_url}/index.php/api/finance.Callback/{endpoint}"
        headers = {
            "User-Agent": "AdsManager/1.0",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {str(e)}")
            return {"code": 500, "msg": "网络连接异常"}

    def get_auth_token(self, username, password, keep_days=7):
        """获取访问令牌"""
        params = {
            "username": username,
            "password": password,
            "keep": keep_days,
            "source": self.source
        }
        result = self._request("getAuth", method="GET", params=params)
        if result.get("code") == 200:
            self.token = result.get("data", {}).get("token")
            return True
        print(f"认证失败: {result.get('msg')}")
        return False

    def report_spend(self, account_id, account_name, balance, spend, auth_code):
        """上报消费数据"""
        if not self.token:
            print("请先获取认证令牌")
            return False

        data = {
            "account_id": account_id,
            "account_name": account_name,
            "balance": balance,
            "spend": spend,
            "auth_code": auth_code,
            "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        result = self._request("index", data=data)
        if result.get("code") == 200:
            print("数据上报成功")
            return True
        print(f"上报失败: {result.get('msg')}")
        return False

# 使用示例
if __name__ == "__main__":
    client = ReportClient()
    
    # 第一步：获取令牌
    if client.get_auth_token("admin", "password123"):
        # 第二步：上报数据
        client.report_spend(
            account_id="123456",
            account_name="测试账户",
            balance=1500.00,
            spend=300.00,
            auth_code="2024ADMIN"
        ) 