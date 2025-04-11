from enum import Enum
from pathlib import Path

class TaskType(Enum):
    CHECK_BALANCE = "余额监控"
    CREATE_AD = "创建广告"

class AppConfig:
    """存储全局配置"""
    adspower_path = None

def validate_adspower(path):
    """路径验证逻辑"""
    return (Path(path) / 'ads.exe').exists() 