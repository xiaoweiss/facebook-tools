import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from curl_helper import APIClient
from facebook_operations import click_create_button, select_sales_objective, open_new_tab
from browser_utils import get_active_session
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


def should_process(account_info):
    """判断是否需要处理该广告账户（新版）"""
    return (
            "使用中" in account_info.get("状态", "") and
            "额度" in account_info.get("付款方式", "") and
            account_info.get("asset_id") not in PROCESSED
    )


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


def process_business_accounts(driver, accounts, username):
    """处理所有业务账户（优化导航版）"""
    try:
        # 获取所有账户链接（提前获取避免元素失效）
        account_links = [a.get_attribute('href') for a in accounts]

        for index, link in enumerate(account_links, 1):
            print(f"\n➡️ 正在处理第 {index} 个业务账户")

            # 直接导航代替点击元素
            driver.get(link)

            # 等待页面核心元素加载
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
            )

            # 从URL解析参数（保持原有参数获取方式）
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)
            business_id = query_params['business_id'][0]
            global_scope_id = query_params['global_scope_id'][0]
            print(f"📌 提取参数: business_id={business_id} global_scope_id={global_scope_id}")

            # 保留原有广告账户处理流程
            ad_accounts = parse_ad_accounts_table(driver, business_id, global_scope_id)
            if not ad_accounts:
                print(f"⚠️ 未获取到广告账户，跳过当前业务账户")
                continue

            # 执行原有详细处理流程
            processed = process_qualified_accounts(driver, ad_accounts)

            # 保持原有结果输出
            print("\n🧾 单账户处理结果：")
            report_data = []
            for acc in processed:
                print(f"账户ID: {acc['asset_id']}")
                print(f"账户信息: {acc['account_info']}")
                print(f"  状态: {acc['status']}")
                print(f"  精确余额: {acc['exact_balance']}")
                print(f"  总花费: {acc['total_spend']}")
                print("-" * 40)

                # 构建单个上报条目
                report_data.append({
                    "account_info": acc["account_info"],
                    "asset_id": acc["asset_id"],
                    "status": acc["status"],
                    "exact_balance": acc["exact_balance"],
                    "total_spend": acc["total_spend"]
                })
            # 实例化 API 客户端
            client = APIClient()

            # 调用上报接口
            response = client.report_spend({
                "report": report_data,
                "username": username
            })

            # 输出上报结果
            if response:
                print("📡 消费数据上报成功:", response)
            else:
                print("❌ 消费数据上报失败")

    except Exception as e:
        print(f"❌ 处理流程异常: {str(e)}")
        raise


def process_business_account(driver, account):
    """处理单个业务账户，返回广告账户数据列表"""
    try:
        # 获取第一个业务账户
        # accounts = get_business_accounts(driver)
        # if not accounts:
        #     print("⚠️ 未找到有效业务账户")
        #     return
        #
        # first_account = accounts[0]
        # print(f"\n🔍 开始处理首个业务账户: {first_account['name']}")

        # 从href提取参数
        query = parse_qs(urlparse(account['href']).query)
        business_id = query.get('business_id', [''])[0]
        global_scope_id = query.get('global_scope_id', [''])[0]
        print(f"📌 提取参数: business_id={business_id} global_scope_id={global_scope_id}")

        # 点击进入账户
        print("🖱️ 正在点击业务账户进入详情页...")
        if not click_business_account(driver, account['element']):
            raise Exception("无法进入业务账户详情页")

        # 等待广告账户表格加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
        )
        print("✅ 成功进入广告账户列表页")

        return parse_ad_accounts_table(driver, business_id, global_scope_id)

    except Exception as e:
        print(f"❌ 处理失败: {account['name']}，错误原因: {str(e)}")
        return None


def parse_ad_accounts_table(driver, business_id, global_scope_id):
    """解析广告账户表格（最终修复版）"""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@aria-label,'广告账户')]"))
        )

        accounts = []
        rows = driver.find_elements(By.XPATH, "//table[contains(@aria-label,'广告账户')]//tbody//tr")

        for idx, row in enumerate(rows):
            try:
                # 提取各列数据（列索引根据实际页面结构调整）
                number_cell = row.find_element(By.XPATH, './/td[1]')  # 编号列
                status_cell = row.find_element(By.XPATH, './/td[2]')  # 状态列
                payment_cell = row.find_element(By.XPATH, './/td[3]')  # 付款方式列
                balance_cell = row.find_element(By.XPATH, './/td[4]')  # 余额列

                # 提取asset_id
                asset_id_match = re.search(r'(\d{15,})', number_cell.text)
                if not asset_id_match:
                    print(f"❌ 行{idx + 1} | 无效编号格式: {number_cell.text}")
                    continue
                asset_id = asset_id_match.group(1)

                account_info = {
                    'account_info': number_cell.text,
                    'business_id': business_id,
                    'global_scope_id': global_scope_id,
                    'asset_id': asset_id,
                    'status': status_cell.text.strip(),
                    'payment_method': payment_cell.text.strip(),
                    'balance': balance_cell.text.strip()
                }

                # 简化的日志输出
                if "使用中" in account_info['status'] and "额度" in account_info['payment_method']:
                    print(f"✅ 有效账户 | ID:{asset_id} | 余额:{account_info['balance']}")
                    accounts.append(account_info)
                else:
                    print(f"➖ 跳过账户 | ID:{asset_id} | 原因:状态/付款方式不匹配")

            except Exception as e:
                print(f"❌ 行{idx + 1}解析异常 | {str(e)[:50]}")

        print(f"\n📊 有效账户: {len(accounts)}/{len(rows)}")
        return accounts

    except Exception as e:
        print(f"解析表格失败: {str(e)}")
        return []


def process_qualified_accounts(driver, accounts):
    """处理符合条件的广告账户（时间选择优化版）"""
    processed = []

    for idx, acc in enumerate(accounts):
        try:
            # ================= 余额查询部分 =================
            detail_url = (
                f"https://business.facebook.com/billing_hub/accounts/details/?"
                f"business_id={acc['business_id']}&"
                f"asset_id={acc['asset_id']}&"
                f"global_scope_id={acc['global_scope_id']}&"
                f"placement=standalone&"
                f"selected_view=transactions"
            )
            print(f"\n🔗 进入账户详情页: {detail_url}")
            driver.get(detail_url)

            # 等待余额加载
            balance_element = WebDriverWait(driver, 25).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//div[@role='heading' and contains(text(), '余额：')]"
                ))
            )

            # 提取精确余额
            amount_text = balance_element.text.split('$')[-1].strip()

            exact_balance = float(amount_text)
            acc['exact_balance'] = exact_balance
            print(f"✅ 精确余额: ${exact_balance:.2f}")

            # ================= 广告管理页面 =================
            ads_manager_url = (
                f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?"
                f"act={acc['asset_id']}&"
                f"nav_entry_point=lep_237&"
                f"business_id={acc['business_id']}&"
                f"nav_source=no_referrer"
            )
            print(f"🌐 正在跳转至广告管理页面: {ads_manager_url[:80]}...")
            driver.get(ads_manager_url)

            try:
                # 等待页面核心元素加载
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_3pzj')]"))
                )
                time.sleep(2)

                # ================= 新增广告数据检测 =================
                print("🔍 检测广告数据...")
                footer = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-pagelet='FixedDataTableNew_footerRow']"))
                )

                # 检查是否存在数据行（通过子元素判断）
                if not footer.find_elements(By.XPATH, "./div"):
                    print("⚠️ 未发现广告数据，总花费按$0处理")
                    acc['total_spend'] = 0.00
                    processed.append(acc)
                    continue  # 跳过后续操作

            except TimeoutException:
                print("⏳ 广告数据加载超时，继续执行后续操作")

            # ================= 新增时间筛选操作 =================
            print("⏰ 执行时间筛选操作...")
            try:
                # 点击时间筛选器
                time_filter = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class,'xw3qccf')])[8]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", time_filter)
                ActionChains(driver).move_to_element(time_filter).pause(0.3).click().perform()
                print("✅ 时间筛选器点击成功")
                time.sleep(1.5)

                # 选择昨天范围
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
                print("✅ 昨天范围选择成功")
                time.sleep(1.5)
            except Exception as filter_e:
                print(f"⚠️ 时间筛选失败: {str(filter_e)[:50]}")

            # ================= 增强版横向滚动操作 =================
            print("🔄 执行复合滚动策略...")

            # 策略1：模拟拖拽滚动
            try:
                scroll_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_3h1k _3h1m')]"))
                )
                thumb = scroll_container.find_element(By.CSS_SELECTOR, '._1t0w')
                track_width = scroll_container.size['width']
                thumb_width = thumb.size['width']

                ActionChains(driver) \
                    .click_and_hold(thumb) \
                    .move_by_offset(track_width - thumb_width, 0) \
                    .pause(0.5) \
                    .release() \
                    .perform()
                print("✅ 拖拽滚动完成")
            except Exception as e:
                print(f"⚠️ 拖拽滚动失败: {str(e)[:50]}")
            time.sleep(1)

            # ================= 智能定位总花费 =================
            print("🔍 执行智能定位...")
            total_spend = None

            try:
                elements = driver.find_elements(By.XPATH, "//span[contains(@class,'_3dfi')]")
                if elements:
                    last_element = elements[-1]
                    total_spend = float(last_element.text.replace('$', '').replace(',', ''))
                    print("✅ 使用列表最后一个元素定位方案")
                else:
                    print("⚠️ 没有找到符合条件的元素")
            except Exception as e:
                print(f"❌ 定位失败: {str(e)[:50]}")

            acc['total_spend'] = total_spend
            print(f"✅ 总花费: ${total_spend:.2f}")

            processed.append(acc)

        except WebDriverException as e:
            if "no such window" in str(e):
                print("‼️ 窗口异常，尝试恢复会话...")
                driver = recover_browser_session(driver, get_active_session(USER_ID))
                return process_qualified_accounts(driver, accounts[idx:])
            raise

    return processed


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


