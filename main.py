import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from curl_helper import APIClient
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session
from task_utils import TaskType, get_billing_info
from fb_billing_operations import (
    is_window_valid,
    process_business_accounts,
)
from selenium.webdriver.common.by import By

USER_IDS = ["kw4udka"]
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"


def connect_browser(api_data):
    """增强浏览器连接稳定性"""
    chrome_options = Options()

    # 配置调试地址（格式：127.0.0.1:端口）
    debug_address = api_data["ws"]["selenium"]
    if ":" not in debug_address:
        debug_address = f"127.0.0.1:{debug_address}"

    chrome_options.add_experimental_option("debuggerAddress", debug_address)

    # 更新反检测配置（移除非必要参数）
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")

    # 从配置获取路径或使用用户选择路径
    webdriver_path = api_data.get("webdriver") or get_config('adspower_path')
    service = Service(executable_path=webdriver_path)

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


def execute_task(driver, task_type, username):
    """执行指定类型任务"""
    if task_type == TaskType.CREATE_AD:
        # 广告创建逻辑...
        if click_create_button(driver):
            select_sales_objective(driver)
    elif task_type == TaskType.CHECK_BALANCE:
        check_balance_operation(driver, username)

def check_balance_operation(driver, username):
    """处理所有业务账户，逐个获取并输出广告账户余额等信息"""
    current_handle = driver.current_window_handle

    try:
        driver.get("https://business.facebook.com/billing_hub/accounts")

        if not is_window_valid(driver):
            raise WebDriverException("主窗口已失效")

        # 获取账户元素后立即处理（避免元素失效）
        account_elements = driver.find_elements(By.XPATH, "//a[contains(@href,'billing_hub/accounts')]")

        # 执行优化后的处理流程（保持原有业务逻辑）
        process_business_accounts(driver, account_elements, username)

    except WebDriverException as e:
        print(f"🚨 窗口异常: {str(e)}")
        driver.switch_to.window(current_handle)


def main_operation(task_type, username):
    try:
        for user_id in USER_IDS:
            try:
                print(f"\n👉 当前账户：{user_id}")
                session_data = get_active_session(user_id)
                driver = connect_browser(session_data)
                open_new_tab(driver)
                execute_task(driver, task_type, username)
                print(f"✅ {user_id} 操作完成")
            except Exception as e:
                print(f"❌ {user_id} 操作失败: {str(e)}")
        input("\n全部账户操作完成，按回车退出...")
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")


if __name__ == '__main__':
    print("🚀 Facebook自动化工具 v1.0")
    # 实例化 API 客户端
    client = APIClient()

    # 鉴权循环
    while True:
        username = input("请输入授权账号: ").strip()
        response = client.get_auth_token(username)

        if response and response.get('code') == 1:
            break  # 成功跳出循环
        else:
            print("❌ 授权失败，请重新输入")





    print("请选择要执行的任务：")
    print("1. 查询账户余额")
    print("2. 创建广告活动")
    task_choice = input("请输入选项数字（1/2）: ").strip()
    if task_choice == "1":
        main_operation(TaskType.CHECK_BALANCE, username)
    elif task_choice == "2":
        main_operation(TaskType.CREATE_AD, username)
    else:
        print("❌ 无效的选项")


