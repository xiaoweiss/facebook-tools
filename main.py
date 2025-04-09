import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session
from task_utils import TaskType, get_billing_info
from fb_billing_operations import (
    get_business_accounts,
    click_business_account,
    is_window_valid,
    get_ad_accounts,
    process_ad,
    click_business_account,
    process_first_account,
    process_qualified_accounts
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import re

USER_ID = "kw4udka"
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

    # 配置WebDriver服务
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


def execute_task(driver, task_type):
    """执行指定类型任务"""
    if task_type == TaskType.CREATE_AD:
        # 广告创建逻辑...
        if click_create_button(driver):
            select_sales_objective(driver)
    elif task_type == TaskType.CHECK_BALANCE:
        check_balance_operation(driver)


def take_screenshot(driver, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_{name}_{timestamp}.png"
    driver.save_screenshot(filename)
    print(f"⚠️ 已保存截图: {filename}")


def should_process(account_info):
    """判断是否需要处理该广告账户"""
    return (
            "使用中" in account_info.get("状态", "") and
            "额度" in account_info.get("付款方式", "") and
            account_info.get("asset_id", "") not in PROCESSED_ACCOUNTS
    )


def check_balance_operation(driver):
    """保留业务账户处理框架"""
    current_handle = driver.current_window_handle

    try:
        driver.get("https://business.facebook.com/billing_hub/accounts")

        if not is_window_valid(driver):
            raise WebDriverException("主窗口已失效")

        # 处理业务账户并获取广告账户
        raw_accounts = process_first_account(driver)
        if raw_accounts:
            processed_accounts = process_qualified_accounts(driver, raw_accounts)
        else:
            processed_accounts = []

        if processed_accounts:
            print("\n📝 处理结果汇总:")
            for acc in processed_accounts:
                print(f"账户ID: {acc['asset_id']}")
                print(f"  状态: {acc['status']}")
                print(f"  原始余额: {acc['balance']}")
                exact_balance = acc.get('exact_balance')
                if isinstance(exact_balance, (int, float)):
                    print(f"  精确余额: ${exact_balance:.2f}")
                else:
                    print(f"  精确余额: {exact_balance or 'N/A'}")
                print("-" * 40)

    except WebDriverException as e:
        print(f"窗口异常: {str(e)}")
        driver.switch_to.window(current_handle)
        take_screenshot(driver, "window_crash")


def check_network(driver):
    try:
        driver.execute_script("return navigator.onLine")
    except:
        return False
    return True


def main_operation(task_type):
    try:
        session_data = get_active_session(USER_ID)
        driver = connect_browser(session_data)
        open_new_tab(driver)
        execute_task(driver, task_type)
        input("操作完成，按回车退出...")
    except Exception as e:
        print(f"操作失败: {str(e)}")


def balance_check(driver):
    """余额检查主流程"""
    for biz in get_businesses(driver):
        try:
            ActionChains(driver).click(biz['element']).perform()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//table[contains(@aria-label,'广告账户')] | //div[contains(.,'无广告账户')]"
                                                ))
            )
            process_ad(driver, biz['id'])
        finally:
            driver.back()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("🚀 Facebook自动化工具 v1.0")
    print("请选择要执行的任务：")
    print("1. 查询账户余额")
    print("2. 创建广告活动")

    task_choice = input("请输入选项数字（1/2）: ").strip()

    if task_choice == "1":
        main_operation(TaskType.CHECK_BALANCE)
    elif task_choice == "2":
        main_operation(TaskType.CREATE_AD)
    else:
        print("❌ 无效的选项")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
