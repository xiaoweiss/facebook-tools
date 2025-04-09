import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session, connect_browser, initialize_new_browser
from task_utils import TaskType, get_billing_info
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse
import time

USER_ID = "kw4udka"
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"

PROCESSED = set()


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
    """判断是否需要处理该广告账户（新版）"""
    return (
            "使用中" in account_info.get("状态", "") and
            "额度" in account_info.get("付款方式", "") and
            account_info.get("原始余额", 0) <= 1000 and
            account_info.get("asset_id") not in PROCESSED
    )


def check_balance_operation(driver):
    """保留业务账户处理框架"""
    current_handle = driver.current_window_handle

    try:
        driver.get("https://business.facebook.com/billing_hub/accounts")

        if not is_window_valid(driver):
            raise WebDriverException("主窗口已失效")

        business_accounts = get_business_accounts(driver)

        print(f"\n发现 {len(business_accounts)} 个业务账户:")
        for idx, acc in enumerate(business_accounts, 1):
            print(f"{idx}. {acc['name']} (广告账户: {acc['id']} 个)")

        for account in business_accounts:
            business_id = account['id']

            for attempt in range(3):
                try:
                    if process_ad(driver, business_id):
                        break

                except Exception as e:
                    print(f"第{attempt + 1}次尝试失败: {str(e)}")
                    driver.refresh()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table.uiGrid._51mz"))
                    )

            if attempt == 2:
                print(f"⚠️ 跳过 {account['name']} 因多次尝试失败")

    except WebDriverException as e:
        print(f"窗口异常: {str(e)}")
        driver.switch_to.window(current_handle)
        take_screenshot(driver, "window_crash")
        if not is_window_valid(driver):
            driver = initialize_new_browser(get_active_session(USER_ID))


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

def get_business_accounts(driver):
    """获取所有业务账户的链接和信息"""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class,'uiGrid _51mz')]"))
        )

        accounts = []
        rows = driver.find_elements(By.XPATH, "//tr[@class='_51mx']")

        for row in rows:
            cells = row.find_elements(By.XPATH, ".//td[@class='_2ph- _51m-'] | .//td[@class='_2ph- _51mw _51m-']")

            for cell in cells:
                try:
                    link = cell.find_element(By.XPATH, ".//a[contains(@class,'_5hw8')]")
                    href = link.get_attribute('href')

                    # 提取业务账户名称
                    name_span = link.find_element(By.XPATH, ".//span[contains(@style,'color: rgb(55, 55, 55)')]")
                    name = name_span.text

                    # 提取统计信息
                    stats_div = link.find_element(By.XPATH, ".//div[contains(@style,'color: rgb(141, 148, 158)')]")
                    stats_text = stats_div.text

                    accounts.append({
                        'name': name,
                        'href': href,
                        'stats': {
                            'ad_accounts': re.search(r'(\d+)个广告账户', stats_text).group(1),
                            'pages': re.search(r'(\d+)个公共主页', stats_text).group(1),
                            'users': re.search(r'(\d+)位用户', stats_text).group(1)
                        },
                        'element': link  # 添加元素引用
                    })
                except Exception as e:
                    print(f"解析单元格失败: {str(e)}")
                    continue

        print(f"共找到 {len(accounts)} 个业务账户:")
        for idx, acc in enumerate(accounts, 1):
            print(f"{idx}. {acc['name']}")
            print(f"  链接: {acc['href']}")
            print(f"  统计: {acc['stats']}")
            print("-" * 50)

        return accounts

    except Exception as e:
        print(f"获取业务账户失败: {str(e)}")
        take_screenshot(driver, "business_accounts_error")
        return []


def click_business_account(driver, element):
    """点击业务账户（增强版）"""
    try:
        print(f"🖱️ 正在点击业务账户: {element.text}")
        ActionChains(driver).move_to_element(element).click().perform()

        # 验证页面跳转
        WebDriverWait(driver, 15).until(
            lambda d: "billing_hub/accounts" in d.current_url
        )
        print(f"✅ 成功跳转至: {driver.current_url}")
        return True

    except Exception as e:
        print(f"❌ 点击业务账户失败: {str(e)}")
        take_screenshot(driver, "click_business_error")
        return False


def process_ad(driver, biz_id):
    """广告账户核心处理逻辑"""
    try:
        # 等待并获取有效账户行
        rows = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH,
                                                 "//tr[.//*[contains(text(),'用中')] and .//*[contains(text(),'额度')]]"
                                                 ))
        )

        if rows:
            # 处理第一个有效账户
            row = rows[0]
            btn = row.find_element(By.XPATH, ".//div[contains(.,'查看详情')]")
            ActionChains(driver).click(btn).perform()

            # 验证跳转结果
            WebDriverWait(driver, 10).until(
                EC.url_contains("payment_methods") |
                EC.url_contains("billing/")
            )

            # 使用asset_id替代账户名称
            asset_id = re.search(r'\d{15}', row.text).group()
            PROCESSED.add(f"{biz_id}_{asset_id}")
            return True
        return False

    except Exception as e:
        print(f"处理异常: {str(e)}")
        return False


def is_window_valid(driver):
    """验证窗口句柄有效性"""
    try:
        driver.current_url
        return True
    except WebDriverException:
        return False


def get_ad_accounts(driver):
    """获取广告账户列表（清理版）"""
    return [{
        "状态": row.find_element(By.XPATH, './/td[2]').text,
        "付款方式": row.find_element(By.XPATH, './/td[3]').text
    } for row in driver.find_elements(
        By.XPATH, "//table[contains(@aria-label,'广告账户')]//tbody//tr")
    ]


def process_account_by_id(driver, business_id, account_id, scope_id):
    """处理指定广告账户"""
    # 实现具体的账户处理逻辑
    return 0.0  # 返回示例值


def process_first_account(driver):
    """处理第一个业务账户"""
    try:
        # 获取第一个业务账户
        accounts = get_business_accounts(driver)
        if not accounts:
            print("⚠️ 未找到有效业务账户")
            return

        first_account = accounts[0]
        print(f"\n🔍 开始处理首个业务账户: {first_account['name']}")

        # 从href提取参数
        query = parse_qs(urlparse(first_account['href']).query)
        business_id = query.get('business_id', [''])[0]
        global_scope_id = query.get('global_scope_id', [''])[0]
        print(f"📌 提取参数: business_id={business_id} global_scope_id={global_scope_id}")

        # 点击进入账户
        print("🖱️ 正在点击业务账户进入详情页...")
        if not click_business_account(driver, first_account['element']):
            raise Exception("无法进入业务账户详情页")

        # 等待广告账户表格加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
        )
        print("✅ 成功进入广告账户列表页")

        return parse_ad_accounts_table(driver, business_id, global_scope_id)

    except Exception as e:
        print(f"处理首个账户失败: {str(e)}")
        take_screenshot(driver, "first_account_error")
        return None


def parse_ad_accounts_table(driver, business_id, global_scope_id):
    """解析广告账户表格"""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
        )

        accounts = []
        rows = driver.find_elements(By.XPATH, "//table[contains(@aria-label,'广告账户')]//tbody//tr")

        for idx, row in enumerate(rows):
            try:
                # 提取账户信息逻辑...
                # 示例实现：
                asset_id = re.search(r'\d{15}', row.text).group()
                accounts.append({
                    'business_id': business_id,
                    'global_scope_id': global_scope_id,
                    'asset_id': asset_id,
                    'status': '使用中',
                    'payment_method': '额度'
                })
            except Exception as e:
                print(f"行解析失败: {str(e)}")

        return accounts

    except Exception as e:
        print(f"表格解析失败: {str(e)}")
        return []


def process_qualified_accounts(driver, accounts):
    """处理符合条件的广告账户（集成时间筛选版）"""
    processed = []
    
    for acc in accounts:
        try:
            # ================= 余额查询部分 =================
            detail_url = build_detail_url(acc)
            print(f"\n🔗 进入账户详情页: {detail_url}")
            driver.get(detail_url)

            # 获取精确余额
            exact_balance = get_exact_balance(driver)
            acc['exact_balance'] = exact_balance
            print(f"✅ 精确余额: ${exact_balance:.2f}")

            # ================= 广告管理页面操作 =================
            navigate_to_ads_manager(driver, acc)
            apply_time_filter(driver)
            
            processed.append(acc)
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            continue
            
    return processed

def build_detail_url(account_info):
    """构建账户详情页URL"""
    return (
        f"https://business.facebook.com/billing_hub/accounts/details/?"
        f"business_id={account_info['business_id']}&"
        f"asset_id={account_info['asset_id']}&"
        f"global_scope_id={account_info['global_scope_id']}&"
        f"placement=standalone&"
        f"selected_view=transactions"
    )

def get_exact_balance(driver):
    """获取精确余额"""
    balance_element = WebDriverWait(driver, 25).until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//div[@role='heading' and contains(text(), '余额：')]"
        ))
    )
    amount_text = balance_element.text.split('$')[-1].strip()
    return float(amount_text)

def navigate_to_ads_manager(driver, account_info):
    """跳转至广告管理页面"""
    ads_manager_url = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={account_info['asset_id']}&nav_entry_point=lep_237"
    print(f"🌐 正在跳转至广告管理页面: {ads_manager_url[:80]}...")
    driver.get(ads_manager_url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_3pzj')]"))
    )
    time.sleep(2)

def apply_time_filter(driver):
    """应用时间筛选器"""
    print("🗓️ 定位时间筛选器...")
    time_filter = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class,'xw3qccf')])[8]"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", time_filter)
    ActionChains(driver).move_to_element(time_filter).pause(0.3).click().perform()
    print("✅ 时间筛选器点击成功")
    time.sleep(1.5)

    print("🕒 选择昨天范围...")
    yesterday_radio = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//input[@type='radio' and @value='yesterday']"
            "/ancestor::div[contains(@class,'x1n2onr6')]"
            "//div[contains(text(),'昨天')]"
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", yesterday_radio)
    ActionChains(driver).move_to_element(yesterday_radio).click().perform()
    
    WebDriverWait(driver, 3).until(
        lambda d: d.find_element(By.XPATH, "//input[@value='yesterday']")
                 .get_attribute('aria-checked') == 'true'
    )
    print("✅ 昨天范围选择成功")
    time.sleep(1)
