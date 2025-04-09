import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session, connect_browser
from task_utils import TaskType, get_billing_info
from fb_billing_operations2 import check_balance_operation
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import re

USER_ID = "kw4udka"
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"


def execute_task(driver, task_type):
    """执行指定类型任务"""
    if task_type == TaskType.CREATE_AD:
        # 广告创建逻辑...
        if click_create_button(driver):
            select_sales_objective(driver)
    elif task_type == TaskType.CHECK_BALANCE:
        check_balance_operation(driver)


def should_process(account_info):
    """判断是否需要处理该广告账户"""
    return (
            "使用中" in account_info.get("状态", "") and
            "额度" in account_info.get("付款方式", "") and
            account_info.get("原始余额", 0) <= 1000 and
            account_info.get("asset_id", "") not in PROCESSED_ACCOUNTS
    )


def main_operation(task_type):
    try:
        session_data = get_active_session(USER_ID)
        driver = connect_browser(session_data)
        open_new_tab(driver)
        execute_task(driver, task_type)
        input("操作完成，按回车退出...")
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")


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
