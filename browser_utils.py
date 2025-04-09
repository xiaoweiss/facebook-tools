import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

def get_active_session(user_id):
    """通用获取浏览器会话信息"""
    try:
        active_res = requests.get(
            f"http://127.0.0.1:50325/api/v1/browser/active?user_id={user_id}",
            timeout=5
        )
        if active_res.json().get("code") != 0:
            raise ConnectionError("浏览器未处于活动状态")

        start_res = requests.get(
            f"http://127.0.0.1:50325/api/v1/browser/start?user_id={user_id}"
        )
        return start_res.json()["data"]
    except requests.exceptions.ConnectionError:
        print("无法连接到ADSPower API")
        raise

def connect_browser(api_data):
    """增强浏览器连接稳定性"""
    chrome_options = Options()

    # 配置调试地址（格式：127.0.0.1:端口）
    debug_address = api_data["ws"]["selenium"]
    if ":" not in debug_address:
        debug_address = f"127.0.0.1:{debug_address}"

    chrome_options.add_experimental_option("debuggerAddress", debug_address)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")

    service = Service(
        executable_path=api_data["webdriver"],
        service_args=["--log-path=chromedriver.log"]
    )

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"✅ 成功连接到浏览器实例 | 调试端口: {debug_address}")
        return driver
    except WebDriverException as e:
        print(f"‼️ 连接失败: {str(e)}")
        if "no such window" in str(e):
            print("🔄 尝试重新初始化浏览器会话...")
            return initialize_new_browser(api_data)
        raise

def initialize_new_browser(api_data):
    """创建新的浏览器实例"""
    print("🚀 启动全新浏览器实例...")
    service = Service(executable_path=api_data["webdriver"])
    return webdriver.Chrome(service=service)

def recover_browser_session(driver, session_data):
    """恢复浏览器会话"""
    try:
        driver.quit()
    except:
        pass
    print("�� 正在重新初始化浏览器会话...")
    new_driver = connect_browser(session_data)
    return new_driver 