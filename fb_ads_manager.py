import requests
from playwright.sync_api import sync_playwright

USER_ID = "kw4udka"
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"

def check_browser_status():
    try:
        # 检测浏览器状态
        status_response = requests.get(
            f"http://local.adspower.net:50325/api/v1/browser/active?user_id={USER_ID}"
        )
        
        if status_response.json().get("code") == 0:
            # 获取浏览器连接信息
            start_response = requests.get(
                f"http://local.adspower.net:50325/api/v1/browser/start?user_id={USER_ID}"
            )
            
            ws_url = start_response.json().get("data", {}).get("ws", {}).get("puppeteer")
            if ws_url:
                with sync_playwright() as p:
                    # 连接浏览器
                    browser = p.chromium.connect_over_cdp(ws_url)
                    page = browser.new_page()
                    
                    # 导航到目标页面
                    page.goto(TARGET_URL, wait_until="networkidle")
                    print("成功打开广告管理页面")
                    
                    # 保持浏览器打开（根据需求调整）
                    # input("按回车键关闭浏览器...")
                    # browser.close()
            else:
                print("获取WebSocket连接失败")
        else:
            print("浏览器未运行，请先启动浏览器")
    except Exception as e:
        print(f"操作失败: {str(e)}")

if __name__ == "__main__":
    check_browser_status() 