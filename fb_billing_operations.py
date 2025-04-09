import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session
from task_utils import get_billing_info
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse
import time
from enum import Enum

USER_ID = "kw4udka"
TARGET_URL = "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet"

PROCESSED = set()

class TaskType(Enum):
    CHECK_BALANCE = 1
    CREATE_AD = 2


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


def should_process(account_info):
    """判断是否需要处理该广告账户（增强版）"""
    required_fields = ['status', 'payment_method', 'asset_id']
    
    # 验证必要字段存在
    if any(field not in account_info for field in required_fields):
        print(f"⚠️ 账户信息缺失关键字段: {account_info}")
        return False
    
    # 验证字段值
    status_ok = account_info['status'] == "使用中"
    payment_ok = account_info['payment_method'] == "额度"
    not_processed = account_info['asset_id'] not in PROCESSED
    
    if not status_ok:
        print(f"➖ 跳过账户 {account_info['asset_id']}: 状态不符合")
    if not payment_ok:
        print(f"➖ 跳过账户 {account_info['asset_id']}: 付款方式不符合")
    if not not_processed:
        print(f"➖ 跳过账户 {account_info['asset_id']}: 已处理过")
    
    return status_ok and payment_ok and not_processed


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
        if not is_window_valid(driver):
            driver = initialize_new_browser(get_active_session(USER_ID))


def main_operation(task_type, account_info=None):
    try:
        session_data = get_active_session(USER_ID)
        driver = connect_browser(session_data)
        open_new_tab(driver)
        execute_task(driver, task_type)
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")

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
        return []


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

        # ================= 强制导航到广告账户列表页 =================
        print("🌐 正在强制跳转到广告账户列表页...")
        ad_accounts_url = f"https://business.facebook.com/billing_hub/accounts?business_id={business_id}&global_scope_id={global_scope_id}"
        driver.get(ad_accounts_url)
        
        # 使用更可靠的等待条件
        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'广告账户')] | //div[contains(text(),'无广告账户')]"))
            )
            print("✅ 成功加载广告账户列表")
        except TimeoutException:
            print("⏳ 广告账户列表加载超时")
            return []
        except Exception as e:
            print(f"❌ 广告账户列表加载失败: {str(e)}")
            return []

        # 等待广告账户表格加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
        )

        # ================= 核心修改点 =================
        # 解析广告账户表格
        ad_accounts = parse_ad_accounts_table(driver, business_id, global_scope_id)
        print("\n=== 解析到的广告账户 ===")
        for idx, acc in enumerate(ad_accounts, 1):
            print(f"{idx}. ID: {acc['asset_id']}")
            print(f"   状态: {acc['status']}")
            print(f"   付款方式: {acc['payment_method']}")
            print(f"   余额: {acc['balance']}")
        print("="*40 + "\n")

        # 执行后续业务处理
        if ad_accounts:
            process_qualified_accounts(driver, ad_accounts)
        else:
            print("⚠️ 无有效广告账户可供处理")
        # ================= 修改结束 =================

    except Exception as e:
        print(f"处理首个业务账户失败: {str(e)}")
        driver.save_screenshot("first_account_error.png")


def parse_ad_accounts_table(driver, business_id, global_scope_id):
    """解析广告账户表格（增强稳定版）"""
    try:
        # 使用更稳定的等待条件
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]//th[contains(.,'编号')]"))
        )

        accounts = []
        rows = driver.find_elements(By.XPATH, "//table[contains(@aria-label,'广告账户')]//tbody//tr")
        print(f"发现 {len(rows)} 行广告账户数据")

        for idx, row in enumerate(rows, 1):
            try:
                # 使用相对定位提高稳定性
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) < 4:
                    print(f"❌ 行{idx} | 列数不足: {len(cells)}/4")
                    continue

                # 提取各列数据
                number_cell = cells[0]
                status_cell = cells[1]
                payment_cell = cells[2]
                balance_cell = cells[3]

                # 提取asset_id（增强匹配模式）
                asset_id_match = re.search(r'\b\d{14,16}\b', number_cell.text)
                if not asset_id_match:
                    print(f"❌ 行{idx} | 无效编号格式: {number_cell.text}")
                    continue
                asset_id = asset_id_match.group()

                account_info = {
                    'business_id': business_id,
                    'global_scope_id': global_scope_id,
                    'asset_id': asset_id,
                    'status': status_cell.text.strip(),
                    'payment_method': payment_cell.text.strip(),
                    'balance': balance_cell.text.strip(),
                    'raw_data': {  # 添加原始数据用于调试
                        'number': number_cell.text,
                        'status': status_cell.text,
                        'payment': payment_cell.text,
                        'balance': balance_cell.text
                    }
                }

                # 有效性预筛选
                if account_info['status'] == "使用中" and "额度" in account_info['payment_method']:
                    print(f"✅ 行{idx} | 有效账户 ID:{asset_id}")
                    accounts.append(account_info)
                else:
                    print(f"➖ 行{idx} | 跳过 ID:{asset_id} 原因: "
                        f"状态={account_info['status']} 付款方式={account_info['payment_method']}")

            except Exception as e:
                print(f"⚠️ 行{idx}解析异常: {str(e)[:50]}")
                driver.save_screenshot(f"table_row_error_{idx}.png")

        print(f"\n📊 有效账户统计: 共{len(accounts)}/{len(rows)} 符合条件")
        return accounts

    except TimeoutException:
        print("⏳ 广告账户表格加载超时")
        return []
    except Exception as e:
        print(f"❌ 表格解析严重错误: {str(e)}")
        driver.save_screenshot("table_parse_fatal.png")
        return []

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


def process_qualified_accounts(driver, accounts):
    processed = []
    
    for acc in accounts:
        if not should_process(acc):
            continue
        try:
            print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] 开始处理账户 {acc['asset_id']}")
            
            # ================= 步骤1：进入广告列表页 =================
            ads_manager_url = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={acc['asset_id']}"
            print(f"🌐 正在跳转至广告管理页面: {ads_manager_url[:60]}...")
            driver.get(ads_manager_url)
            print(f"✅ 页面加载完成 | 当前URL: {driver.current_url[:60]}...")

            # ================= 步骤2：解析广告账户列表 =================
            print("📋 正在解析广告账户列表...")
            ad_accounts = parse_ad_accounts_list(driver)
            if not ad_accounts:
                print("⚠️ 未找到有效广告账户，跳过处理")
                acc['total_spend'] = 0.00
                processed.append(acc)
                continue
            print(f"✅ 发现 {len(ad_accounts)} 个广告账户")

            # ================= 步骤3：执行有效性判断 =================
            valid_accounts = []
            for ad_acc in ad_accounts:
                if should_process_ad_account(ad_acc):
                    valid_accounts.append(ad_acc)
                    print(f"✅ 有效广告账户: {ad_acc['account_id']}")
                else:
                    print(f"➖ 跳过无效账户: {ad_acc['account_id']} (状态: {ad_acc['status']})")
            
            if not valid_accounts:
                print("⚠️ 无有效广告账户，跳过处理")
                acc['total_spend'] = 0.00
                processed.append(acc)
                continue

            # ================= 步骤4：处理第一个有效账户 =================
            target_account = valid_accounts[0]
            print(f"🔍 开始处理广告账户 {target_account['account_id']}")
            ActionChains(driver).click(target_account['element']).perform()
            
            # 等待详情页加载
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'账户详情')]"))
            )

            # ================= 步骤3：进入详情页获取余额 =================
            detail_url = build_detail_url(acc)
            print(f"🔗 进入详情页获取余额: {detail_url}")
            driver.get(detail_url)

            # 获取精确余额
            exact_balance = get_exact_balance(driver)
            acc['exact_balance'] = exact_balance
            print(f"✅ 精确余额: ${exact_balance:.2f}")

            # 返回广告列表页
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_3pzj')]"))
            )

            # ================= 步骤4：广告数据检测 =================
            if not check_ad_data_exists(driver):
                print("⚠️ 未发现广告数据，总花费按0处理")
                acc['total_spend'] = 0.00
                processed.append(acc)
                continue

            # ================= 步骤5：时间筛选操作 =================
            apply_time_filter(driver)

            # ================= 步骤6：横向滚动 =================
            perform_horizontal_scroll(driver)

            # ================= 步骤7：获取总花费 =================
            total_spend = locate_total_spend(driver)
            acc['total_spend'] = total_spend
            print(f"✅ 总花费: ${total_spend:.2f}")

            # ================= 结果汇总 =================
            processed.append(acc)
            print(f"\n📊 账户 {acc['asset_id']} 处理完成")
            print(f"   余额: ${exact_balance:.2f}")
            print(f"   总花费: ${total_spend:.2f}")
            print("-"*50)

        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            continue
            
    return processed


def verify_valid_ad_account(driver):
    """验证有效广告账户"""
    try:
        print("🕵️ 正在验证账户有效性...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='有效账户']"))
        )
        print("✅ 有效账户验证通过")
        return True
    except TimeoutException:
        print("⏳ 未检测到有效账户标识")
        return False


def recover_browser_session(driver, session_data):
    """恢复浏览器会话"""
    try:
        driver.quit()
    except:
        pass

    print("🔄 正在重新初始化浏览器会话...")
    new_driver = connect_browser(session_data)
    new_driver.get(TARGET_URL)  # 重新导航到目标页面
    return new_driver


def click_business_account(driver, element):
    """点击业务账户（增强稳定性版）"""
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
        return False


def is_window_valid(driver):
    """验证窗口句柄有效性"""
    try:
        driver.current_url  # 简单验证窗口是否有效
        return True
    except WebDriverException:
        return False


def get_total_spend_via_api(asset_id):
    """通过API获取总花费"""
    try:
        session = requests.Session()
        response = session.get(
            f"https://adsmanager.facebook.com/api/getStats",
            params={"act": asset_id, "time_range": "last_30d"}
        )
        if response.status_code == 200:
            return response.json().get('total_spend', 0.0)
        return None
    except Exception as e:
        print(f"API请求失败: {str(e)}")
        return None


def highlight_element(driver, element):
    """高亮元素用于调试（增强版）"""
    original_style = element.get_attribute("style")
    driver.execute_script(
        "arguments[0].setAttribute('style', arguments[1]);",
        element,
        "border: 3px solid #00ff00 !important; box-shadow: 0 0 10px rgba(0,255,0,0.5) !important;"  # 使用绿色高亮更醒目
    )
    time.sleep(0.5)
    driver.execute_script(
        "arguments[0].setAttribute('style', arguments[1]);",
        element,
        original_style
    )


def parse_ad_accounts_list(driver):
    """解析广告账户列表（增强稳定性版）"""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_8tk7')]"))  # 列表容器
        )
        accounts = []
        rows = driver.find_elements(By.XPATH, "//div[contains(@class,'_8tk7')]//div[@role='row']")
        
        for row in rows:
            try:
                # 使用更稳定的定位方式
                account_id = row.find_element(By.XPATH, ".//div[contains(@class,'_8tk8')]").text
                status = row.find_element(By.XPATH, ".//div[contains(@class,'_8tk9')]").text
                accounts.append({
                    'account_id': re.search(r'\d{15}', account_id).group(),
                    'status': status,
                    'element': row
                })
            except Exception as e:
                print(f"⚠️ 列表项解析失败: {str(e)[:50]}")
        return accounts
    except TimeoutException:
        print("⏳ 广告账户列表加载超时")
        return []
    except Exception as e:
        print(f"❌ 列表解析失败: {str(e)}")
        return []


def should_process_ad_account(ad_account):
    """判断广告账户是否有效"""
    return (
        ad_account.get('status') == "有效" 
        and ad_account.get('account_id') not in PROCESSED
    )

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

def check_ad_data_exists(driver):
    """检测广告数据存在性"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-pagelet='FixedDataTableNew_footerRow']"))
        )
        return True
    except TimeoutException:
        print("⏳ 广告数据加载超时")
        return False

def locate_total_spend(driver):
    """定位总花费金额"""
    try:
        print("🔍 定位总花费元素...")
        total_spend_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//div[contains(text(),'总花费')]/following-sibling::div//div[contains(@class,'x1n2onr6')]"
            ))
        )
        amount_text = total_spend_element.text.replace('$', '').strip()
        return float(amount_text)
    except TimeoutException:
        print("⏳ 总花费元素定位超时")
        return 0.0
    except Exception as e:
        print(f"❌ 获取总花费失败: {str(e)}")
        return 0.0

def perform_horizontal_scroll(driver):
    """执行横向滚动操作（增强版）"""
    print("🔄 开始执行横向滚动...")
    try:
        # 定位滚动容器
        scroll_container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'_8tk7') and contains(@class,'_8tk8')]"
            ))
        )

        # 执行多次滚动确保数据加载
        for _ in range(3):
            driver.execute_script(
                "arguments[0].scrollLeft += 500;",
                scroll_container
            )
            time.sleep(0.5)
            driver.execute_script(
                "arguments[0].scrollLeft -= 300;",
                scroll_container
            )
            time.sleep(0.3)

        print("✅ 横向滚动完成")
    except TimeoutException:
        print("⏳ 滚动容器定位超时")
    except Exception as e:
        print(f"❌ 滚动操作失败: {str(e)}")

def get_ad_accounts(driver):
    """获取广告账户列表（清理版）"""
    return [{
        "状态": row.find_element(By.XPATH, './/td[2]').text,
        "付款方式": row.find_element(By.XPATH, './/td[3]').text
    } for row in driver.find_elements(
        By.XPATH, "//table[contains(@aria-label,'广告账户')]//tbody//tr")
    ]
