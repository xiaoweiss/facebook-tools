import re
import subprocess
from selenium import webdriver

def get_chrome_version():
    """获取ADSPower浏览器版本"""
    try:
        # MacOS路径
        cmd = '/Applications/AdsPower浏览器.app/Contents/MacOS/Chrome --version'
        output = subprocess.check_output(cmd, shell=True).decode()
        return re.search(r'\d+\.\d+\.\d+', output).group()
    except:
        # Windows路径
        cmd = r'"C:\Program Files\AdsPower\chrome.exe" --version'
        output = subprocess.check_output(cmd, shell=True).decode()
        return re.search(r'\d+\.\d+\.\d+', output).group()

def install_matching_driver():
    """自动安装匹配的ChromeDriver"""
    chrome_version = get_chrome_version()
    major_version = chrome_version.split('.')[0]
    
    # 安装最新匹配版本
    subprocess.run(f"pip install chromedriver-py~={major_version}.0.0", shell=True)
    print(f"✅ 已安装匹配 {chrome_version} 的ChromeDriver")

if __name__ == '__main__':
    install_matching_driver() 