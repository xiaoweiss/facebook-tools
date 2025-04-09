from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import platform
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

def click_create_button(driver, timeout=10):
    """点击广告管理页面的创建按钮"""
    try:
        # 使用更稳定的XPath定位方式
        create_btn_xpath = "//div[contains(@class, 'x1xqt7ti') and contains(text(), '创建')]"
        create_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, create_btn_xpath))
        )
        create_btn.click()
        print("✅ 已点击创建按钮")
        return True
    except TimeoutException:
        print("❌ 找不到创建按钮")
        return False

def select_sales_objective(driver, timeout=15):
    """选择销量目标（增强版）"""
    try:
        # 先等待容器加载
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "objectiveContainerOUTCOME_SALES"))
        )
        
        # 复合定位策略
        sales_xpath = '''
        //div[@id='objectiveContainerOUTCOME_SALES']
        //span[contains(@class, 'x1xqt7ti') and text()='销量']
        /ancestor::div[contains(@class, 'x6s0dn4')][1]
        '''
        
        sales_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, sales_xpath))
        )
        
        # 滚动元素到可视区域
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sales_element)
        
        # 带重试的点击操作
        for attempt in range(3):
            try:
                sales_element.click()
                if is_sales_selected(driver):  # 需要添加验证函数
                    print("✅ 已确认选择销量目标")
                    return True
            except Exception as e:
                print(f"点击尝试 {attempt+1}/3 失败: {str(e)}")
                time.sleep(1)
        
        # 最终尝试JS点击
        driver.execute_script("arguments[0].click();", sales_element)
        return True
        
    except Exception as e:
        print(f"❌ 选择销量目标失败: {str(e)}")
        driver.save_screenshot("sales_error.png")
        return False

def is_sales_selected(driver):
    """验证是否成功选择销量目标"""
    try:
        indicator_xpath = "//div[@id='objectiveContainerOUTCOME_SALES']//div[contains(@class, 'x1gzqxud')]"
        indicator = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, indicator_xpath))
        )
        return "x1mh8g0r" in indicator.get_attribute("class")  # 选中状态class
    except:
        return False

def open_new_tab(driver):
    """使用快捷键打开新标签页"""
    # 根据操作系统选择不同的命令键
    modifier_key = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
    
    # 发送快捷键组合
    ActionChains(driver)\
        .key_down(modifier_key)\
        .send_keys('t')\
        .key_up(modifier_key)\
        .perform()
    
    # 等待新标签页出现
    WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
    
    # 切换到新标签页
    driver.switch_to.window(driver.window_handles[-1])
    print("🌐 已打开新标签页")

def get_tab_count(driver):
    """获取当前浏览器标签页数量"""
    return len(driver.window_handles)

def switch_to_tab(driver, index):
    """切换到指定索引的标签页"""
    if 0 <= index < len(driver.window_handles):
        driver.switch_to.window(driver.window_handles[index])
        return True
    return False

def close_current_tab(driver):
    """关闭当前标签页并返回剩余标签页数量"""
    driver.close()
    return len(driver.window_handles) 