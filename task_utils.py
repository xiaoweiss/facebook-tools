from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class TaskType:
    CREATE_AD = 1
    CHECK_BALANCE = 2

def get_billing_info(driver):
    """获取账户余额信息"""
    try:
        # 等待货币单位加载
        currency_span = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, 
                "//span[contains(@class, 'x1lliihq') and contains(text(), '¥') or contains(text(), '$')]"))
        )
        
        # 获取完整金额文本
        amount_div = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,
                "//div[@data-testid='billing_hub_section_account_balance']//div[contains(@class, 'x1n2onr6')]"))
        )
        
        return {
            "currency": currency_span.text.strip(),
            "amount": amount_div.text.split()[0],
            "status": "正常" if "可用" in amount_div.text else "异常"
        }
    except Exception as e:
        print(f"获取余额失败: {str(e)}")
        return None 