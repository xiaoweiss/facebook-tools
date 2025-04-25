import json
import uuid
import hashlib
import datetime
from Crypto.Cipher import AES
import base64
import requests


# === AES 加密前需要做 PKCS7 填充，补齐到16字节倍数 ===
def pad(s):
    block_size = 16
    pad_len = block_size - len(s.encode('utf-8')) % block_size
    return s + chr(pad_len) * pad_len


# === AES-128-CBC 模式加密函数 ===
def aes_encrypt(key, iv, plaintext):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))  # 创建加密器
    padded_text = pad(plaintext)  # 补齐明文
    encrypted = cipher.encrypt(padded_text.encode('utf-8'))  # 加密
    return base64.b64encode(encrypted).decode('utf-8')  # 返回 Base64 编码的密文字符串


# === 生成唯一的 sequenceId，格式为：日期（yyyy-MM-dd）+ 32位GUID ===
def generate_sequence_id():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")  # 获取当前日期
    guid_str = uuid.uuid4().hex  # 生成32位无分隔符GUID
    return f"{date_str}{guid_str}"


# === 按照携程规则拼接字符串并生成 MD5 签名（转小写） ===
def generate_sign(account_id, service_name, request_time, encrypted_body, version, sign_key):
    raw_str = account_id + service_name + request_time + encrypted_body + version + sign_key
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest().lower()


# === 构建完整请求报文 ===
def build_request():
    # 下面是你需要填写的凭证信息，请用携程提供的数据替换
    account_id = "你的accountId"       # 由携程提供
    sign_key = "你的签名Key"           # 携程签名校验用 key
    aes_key = "你的16位AES密钥"        # AES 加密用的 key（16位）
    aes_iv = "你的16位初始化向量IV"     # AES 加密用的 IV（16位）

    # 固定接口信息
    service_name = "DatePriceModify"
    version = "1.0"
    request_time = datetime.datetime