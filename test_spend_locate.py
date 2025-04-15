# import base64
# import hashlib
# import string
# from random import random
# import json
#
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.action_chains import ActionChains
# from fb_billing_operations2 import connect_browser, get_active_session
# import time
# from facebook_operations import click_create_button, select_sales_objective, open_new_tab
# from selenium.common.exceptions import TimeoutException
# import re
# # from curl_helper import CurlGenerator, APIClient
# from urllib.parse import urljoin
#
# # 测试专用配置
# TEST_ACCOUNT = "634690976112979"
# TEST_URL = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={TEST_ACCOUNT}&nav_entry_point=lep_237"
#
# # # 初始化API客户端
# # api_client = APIClient()
# #
# # reporter = CurlGenerator()
# # reporter._load_config('curl_config.json')
#
# def debug_locate_spend(driver):
#     """调试专用定位函数（空数据检测版）"""
#     print("\n=== 调试模式启动 ===")
#
#     account_info = {
#         "account_id": driver.current_url.split('act=')[1].split('&')[0],
#         "account_name": driver.find_element(By.XPATH, "//a[@aria-label='广告账户']").text
#     }
#
#     try:
#         # ================= 广告数据检测 =================
#         print("🔍 检测广告数据...")
#         footer = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, "//div[@data-pagelet='FixedDataTableNew_footerRow']"))
#         )
#
#         if not footer.find_elements(By.XPATH, "./div"):
#             print("⚠️ 未发现广告数据，总花费按$0处理")
#             return 0.00
#
#         # ================= 时间筛选操作 =================
#         print("⏰ 执行时间筛选操作...")
#         try:
#             # 点击时间筛选器
#             time_filter = WebDriverWait(driver, 15).until(
#                 EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class,'xw3qccf')])[8]"))
#             )
#             driver.execute_script("arguments[0].scrollIntoView({block:'center'});", time_filter)
#             ActionChains(driver).move_to_element(time_filter).pause(0.3).click().perform()
#             print("✅ 时间筛选器点击成功")
#             time.sleep(1.5)
#
#             # 选择昨天范围
#             yesterday_radio = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((
#                     By.XPATH,
#                     "//input[@type='radio' and @value='yesterday']"
#                     "/ancestor::div[contains(@class,'x1n2onr6')]"
#                     "//div[contains(text(),'昨天')]"
#                 ))
#             )
#             driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", yesterday_radio)
#             ActionChains(driver).move_to_element(yesterday_radio).click().perform()
#             print("✅ 昨天范围选择成功")
#             time.sleep(1.5)
#         except Exception as filter_e:
#             print(f"⚠️ 时间筛选失败: {str(filter_e)[:50]}")
#
#         # ================= 增强版横向滚动操作 =================
#         print("🔄 执行复合滚动策略...")
#         try:
#             scroll_container = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_3h1k') and contains(@class,'_3h1m')]"))
#             )
#             thumb = scroll_container.find_element(By.CSS_SELECTOR, '._1t0w')
#             track_width = scroll_container.size['width']
#             thumb_width = thumb.size['width']
#
#             # 执行多次滚动确保到最右侧
#             for _ in range(3):
#                 ActionChains(driver) \
#                     .click_and_hold(thumb) \
#                     .move_by_offset(track_width - thumb_width, 0) \
#                     .pause(0.5) \
#                     .release() \
#                     .perform()
#                 print("✅ 拖拽滚动完成")
#                 time.sleep(0.5)
#         except Exception as e:
#             print(f"⚠️ 拖拽滚动失败: {str(e)[:50]}")
#
#         # ================= 智能定位总花费 =================
#         print("🔍 执行智能定位...")
#         try:
#             # 打印所有相关元素
#             debug_elements = driver.find_elements(By.XPATH, "//span[contains(@class,'_3dfi') and contains(@class,'_3dfj')]")
#             print(f"🔄 找到 {len(debug_elements)} 个候选元素:")
#             for idx, elem in enumerate(debug_elements, 1):
#                 print(f"[{idx}] {elem.text} | 坐标: ({elem.location['x']}, {elem.location['y']})")
#
#             # 直接获取最后一个有效元素
#             spend_element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.XPATH, "(//span[contains(@class,'_3dfi') and contains(@class,'_3dfj')])[last()]"))
#             )
#
#             # 增强文本处理
#             raw_text = spend_element.text.replace('$', '').replace(',', '')
#             clean_text = re.search(r'[\d,]+\.?\d*', raw_text).group()
#             total_spend = float(clean_text)
#             print("✅ 使用末位定位方案")
#         except Exception as e:
#             print(f"⚠️ 定位失败: {str(e)[:50]}")
#             # 备用方案：通过列索引定位
#             try:
#                 spend_cell = driver.find_element(By.XPATH, "//div[contains(@class,'_4g34')][last()]//span[contains(@class,'_3dfi')]")
#                 total_spend = float(spend_cell.text.replace('$', '').replace(',', ''))
#                 print("✅ 使用备用定位方案")
#             except:
#                 print("❌ 所有定位方案均失败")
#                 return None
#
#         if total_spend is not None:
#             print(f"✅ 总花费: ${total_spend:.2f}")
#             # 上报数据
#             report_data = {
#                 **account_info,
#                 "balance": 0.0,  # 需要实际余额数据
#                 "spend": total_spend,
#                 "auth_code": generate_license_key(account_info["account_id"])
#             }
#
#             curl_cmd = reporter.generate_curl(
#                 method="POST",
#                 endpoint=API_CONFIG["endpoints"]["report_spend"],
#                 data=report_data
#             )
#             print("\n🔗 生成的上报命令:")
#             print(curl_cmd)
#
#             # 实际执行上报
#             response = reporter._request(
#                 endpoint=API_CONFIG["endpoints"]["report_spend"],
#                 method="POST",
#                 data=report_data
#             )
#             print(f"📤 上报结果: {response.get('msg', '未知状态')}")
#
#             return total_spend
#         return 0.00
#
#     except Exception as e:
#         print(f"❌ 操作失败: {str(e)}")
#         driver.save_screenshot("error.png")
#         return None
#
# def generate_license_key(base_value: str, salt: str = "ZHUZHU") -> str:
#     """基于 base_value 和 salt 生成授权码"""
#     if not salt:
#         salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
#
#     # 将 base_value 转换为字符串类型
#     base_str = str(base_value).upper()
#
#     # 混合数据结构
#     mixed = f"{salt[::-1]}-{base_str}-{salt}"
#
#     # 多轮 hash 混淆
#     sha1 = hashlib.sha1(mixed.encode()).hexdigest()
#     md5 = hashlib.md5(sha1.encode()).hexdigest()
#
#     # 再次 Base64 混淆
#     final_raw = f"{md5[:16]}{salt}{md5[16:]}"
#     license_key = base64.urlsafe_b64encode(final_raw.encode()).decode()
#
#     return license_key
#
# def main_operation(task_type, accounts):
#     try:
#         for user in accounts:
#             print(f"\n=== 开始处理用户 {user} ===")
#             try:
#                 # 先获取认证令牌
#                 auth_token = get_auth_token(user, "password123")  # 需替换实际密码
#                 reporter.config['default_headers']['Authorization'] = f"Bearer {auth_token}"
#
#                 session_data = get_active_session(user)
#                 driver = connect_browser(session_data)
#
#                 # 获取账户基本信息
#                 account_name = driver.find_element(By.XPATH, "//a[@aria-label='广告账户']").text
#                 account_id = driver.current_url.split('act=')[1].split('&')[0]
#
#                 # 执行主要操作
#                 total_spend = debug_locate_spend(driver)
#
#                 print(f"\n✅ 用户 {user} 处理完成")
#                 driver.quit()
#
#             except Exception as e:
#                 print(f"❌ 用户 {user} 处理失败: {str(e)}")
#                 continue
#         input("\n所有用户处理完成，按回车退出...")
#     except Exception as e:
#         print(f"❌ 操作失败: {str(e)}")
#
# def test_authentication():
#     """测试认证接口"""
#     print("\n=== 开始认证测试 ===")
#     result = api_client.get_auth_token("test_user", "test_password")
#
#     if result and result.get("code") == 200:
#         print(f"✅ 认证成功，令牌: {result['data']['token']}")
#         return True
#     else:
#         print(f"❌ 认证失败: {result.get('msg', '未知错误')}")
#         return False
#
# def test_report_spending():
#     """测试数据上报接口"""
#     print("\n=== 开始数据上报测试 ===")
#     test_data = {
#         "account_id": "test_123",
#         "account_name": "测试账户",
#         "balance": 1000.0,
#         "spend": 150.0,
#         "auth_code": generate_license_key("test_123")
#     }
#
#     result = api_client.report_spend(test_data)
#
#     if result and result.get("code") == 200:
#         print("✅ 数据上报成功")
#         return True
#     else:
#         print(f"❌ 上报失败: {result.get('msg', '未知错误')}")
#         return False
#
# # ================= 新增多账户循环处理 =================
# if __name__ == "__main__":
#     # 执行接口测试
#     test_authentication()
#     test_report_spending()
#
#     # 执行主业务流程
#     # main_operation(1)
#
