import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
import os
import json

from curl_helper import APIClient
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session
from task_utils import TaskType, get_billing_info
from fb_billing_operations import (
    is_window_valid,
    process_business_accounts,
)
from selenium.webdriver.common.by import By

# 默认账户，但会被用户输入覆盖
DEFAULT_USER_IDS = ["kw4udka"]
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"

def get_config(key, default=None):
    """获取配置值，如果不存在则返回默认值"""
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_config.json')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get(key, default)
        return default
    except Exception:
        return default

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


def main_operation(task_type, username, user_ids=None):
    """主操作函数，支持指定用户ID列表"""
    if user_ids is None or len(user_ids) == 0:
        user_ids = DEFAULT_USER_IDS
        
    try:
        for user_id in user_ids:
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

    # 获取用户ID列表
    print("\n请输入要处理的账户ID列表，多个ID用逗号分隔")
    print("(直接按回车使用默认账户: kw4udka)")
    user_ids_input = input("账户ID: ").strip()
    
    # 解析用户输入的ID
    user_ids = []
    if user_ids_input:
        user_ids = [id.strip() for id in user_ids_input.split(',') if id.strip()]
    
    if not user_ids:
        print("使用默认账户: kw4udka")
        user_ids = DEFAULT_USER_IDS
    else:
        print(f"将处理以下账户: {', '.join(user_ids)}")

    print("\n请选择要执行的任务：")
    print("1. 查询账户余额")
    print("2. 创建广告活动")
    task_choice = input("请输入选项数字（1/2）: ").strip()
    if task_choice == "1":
        main_operation(TaskType.CHECK_BALANCE, username, user_ids)
    elif task_choice == "2":
        main_operation(TaskType.CREATE_AD, username, user_ids)
    else:
        print("❌ 无效的选项")


