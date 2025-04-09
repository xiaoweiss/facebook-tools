from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from fb_billing_operations2 import highlight_element, connect_browser, get_active_session
import time
from selenium.common.exceptions import TimeoutException

# 测试专用配置
TEST_ACCOUNT = "634690976112979"
TEST_URL = f"https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={TEST_ACCOUNT}&nav_entry_point=lep_237"

def debug_locate_spend(driver):
    """调试专用定位函数（空数据检测版）"""
    print("\n=== 调试模式启动 ===")
    
    try:
        # ================= 广告数据检测 =================
        print("🔍 检测广告数据...")
        footer = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-pagelet='FixedDataTableNew_footerRow']"))
        )
        
        # 检查是否存在数据行
        if not footer.find_elements(By.XPATH, "./div"):
            print("⚠️ 未发现广告数据，总花费按0处理")
            return 0.00
        
        # ================= 原有时间筛选操作 =================
        print("🗓️ 定位时间筛选器...")
        # 恢复原有可靠定位方式
        time_filter = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class,'xw3qccf')])[8]"))
        )
        
        # 恢复必要操作步骤
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", time_filter)
        ActionChains(driver).move_to_element(time_filter).pause(0.3).click().perform()
        print("✅ 时间筛选器点击成功")
        time.sleep(1.5)

        # ================= 日期选择操作 =================
        print("🕒 选择昨天范围...")
        # 保留改进的radio定位逻辑
        yesterday_radio = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//input[@type='radio' and @value='yesterday']"
                "/ancestor::div[contains(@class,'x1n2onr6')]"
                "//div[contains(text(),'昨天')]"
            ))
        )

        # 保留增强点击逻辑
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", yesterday_radio)
        ActionChains(driver).move_to_element(yesterday_radio).click().perform()
        
        # 保留状态验证
        WebDriverWait(driver, 3).until(
            lambda d: d.find_element(By.XPATH, "//input[@value='yesterday']")
                     .get_attribute('aria-checked') == 'true'
        )
        print("✅ 昨天范围选择成功")
        time.sleep(1)

        # ================= 智能定位总花费 =================
        print("🔍 执行智能定位...")
        # ... [原有定位逻辑] ...
        
        return total_spend  # 返回实际定位到的金额

    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        driver.save_screenshot("error.png")
        return 0.00  # 异常情况也返回0

if __name__ == "__main__":
    # 初始化浏览器
    driver = connect_browser(get_active_session("kw4udka"))
    
    try:
        print(f"🌐 正在访问测试页面: {TEST_URL}")
        driver.get(TEST_URL)
        
        # 执行调试流程
        total_spend = debug_locate_spend(driver)
        
    finally:
        input("\n操作完成，按回车退出...")
        driver.quit() 