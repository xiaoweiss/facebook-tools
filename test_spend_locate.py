from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from fb_billing_operations2 import connect_browser, get_active_session
import time
from selenium.common.exceptions import TimeoutException

# 测试专用配置
TEST_ACCOUNT = "634690976112979"
TEST_URL = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={TEST_ACCOUNT}&nav_entry_point=lep_237"


def debug_locate_spend(driver):
    """调试专用定位函数（空数据检测版）"""
    print("\n=== 调试模式启动 ===")

    try:  # 主try块包裹整个函数逻辑
        # ================= 广告数据检测 =================
        print("🔍 检测广告数据...")
        footer = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-pagelet='FixedDataTableNew_footerRow']"))
        )

        if not footer.find_elements(By.XPATH, "./div"):
            print("⚠️ 未发现广告数据，总花费按$0处理")
            return 0.00

        # ================= 时间筛选操作 =================
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

            # 验证选中状态
            WebDriverWait(driver, 3).until(
                lambda d: d.find_element(By.XPATH, "//input[@value='yesterday']")
                          .get_attribute('aria-checked') == 'true'
            )
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
        try:
            elements = driver.find_elements(By.XPATH, "//span[contains(@class,'_3dfi')]")
            rightmost_element = max(elements, key=lambda e: e.location['x'])
            total_spend = float(rightmost_element.text.replace('$', '').replace(',', ''))
            print("✅ 使用坐标定位方案")
        except Exception as e:
            print(f"⚠️ 坐标定位失败: {str(e)[:50]}")

        print(f"✅ 总花费: ${total_spend:.2f}")
        return total_spend

    except TimeoutException:  # 单独处理超时异常
        print("⏳ 广告数据加载超时，继续执行后续操作")
        return 0.00

    except Exception as e:  # 统一异常处理
        print(f"❌ 操作失败: {str(e)}")
        driver.save_screenshot("error.png")
        return 0.00


# ================= 新增多账户循环处理 =================
if __name__ == "__main__":
    # 初始化浏览器
    driver = connect_browser(get_active_session("kw4udka"))

    # 账户ID列表
    account_ids = [
        "634690976112979",
        "614249268431768",
        "471350005942160",
        "1734063287520906",
        "1028979435740411"
    ]

    try:
        for acc_id in account_ids:
            test_url = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={acc_id}&nav_entry_point=lep_237"
            print(f"\n🔁 正在处理账户 {acc_id}")
            print(f"🌐 访问页面: {test_url}")
            driver.get(test_url)

            # 执行调试流程
            total_spend = debug_locate_spend(driver)
            print(f"💰 账户 {acc_id} 总花费: ${total_spend:.2f}")

    finally:
        input("\n操作完成，按回车退出...")
        driver.quit() 