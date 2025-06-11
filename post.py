import requests
import json
import urllib.parse
import base64
import logging
import sys

# --- 配置区 ---
# 定义请求的URL
URL = ""

# 定义请求头 (确保Token有效)
HEADERS = {
    "Host": "cdn.blingcc.eu.org",
    "Accept": "application/json, text/plain, */*",
    "Authorization": "Bearer O2A6VQmfnGcK7J4lu2JqaNhW3U71hySrwW19KnYza2737a09",
    "Content-Language": "zh-CN",
    "Sec-Fetch-Site": "same-origin",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Mode": "cors",
    "Content-Type": "application/json",
    "Origin": "https://cdn.blingcc.eu.org",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/137.0.7151.51 Mobile/15E148 Safari/604.1",
    "Referer": "https://cdn.blingcc.eu.org/588802d8",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty"
}

# --- Telegram Bot 配置 ---
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# 定义配置文件路径
FILE_PATHS = {
    "surge_config": "surge_config.conf",
    "clash_yaml": "clash.yaml",
    "singbox_json": "singbox.json"
}
PROXY_FILE = "output.txt"
REQUEST_TIMEOUT = 15  # 每个代理的请求超时时间（秒）

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def send_telegram_notification(token, chat_id, message, proxy_config=None):
    """
    向指定的 Telegram 用户发送消息。
    :param token: Telegram Bot 的 Token
    :param chat_id: 接收消息用户的 Chat ID
    :param message: 要发送的消息文本
    :param proxy_config: (可选) 用于发送请求的代理配置字典
    """
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'  # 使用 Markdown 格式化消息
    }
    
    proxy_display_info = "无代理 (直接连接)"
    if proxy_config and 'http' in proxy_config:
        proxy_display_info = proxy_config['http']

    try:
        # 使用传入的代理配置发送请求
        logging.info(f"准备通过代理 [{proxy_display_info}] 发送 Telegram 通知...")
        response = requests.post(api_url, json=payload, timeout=10, proxies=proxy_config)
        # 如果请求不成功 (例如, token错误, chat_id无效), 抛出异常
        response.raise_for_status()
        logging.info(f"成功通过代理 [{proxy_display_info}] 发送 Telegram 通知。")
    except requests.exceptions.RequestException as e:
        logging.error(f"通过代理 [{proxy_display_info}] 发送 Telegram 通知失败: {e}")


def parse_proxy_url(proxy_line):
    """
    解析形如 socks://Og%3D%3D@115.214.5.128:11112#Ningbo1 的SOCKS5代理字符串。
    返回 requests 库可用的代理字典，或在解析失败时返回 None。
    """
    try:
        # 移除可能存在的注释部分
        if '#' in proxy_line:
            proxy_line = proxy_line.split('#', 1)[0]
        
        parsed_url = urllib.parse.urlparse(proxy_line.strip())

        if parsed_url.scheme.lower() not in ["socks", "socks5"]:
            logging.warning(f"不支持的代理协议: {parsed_url.scheme} (来自: {proxy_line})")
            return None

        host = parsed_url.hostname
        port = parsed_url.port

        if not host or not port:
            logging.warning(f"无效的主机或端口: {proxy_line}")
            return None

        username = None
        password = None

        if parsed_url.username:
            raw_username_info = parsed_url.username
            try:
                decoded_userinfo = base64.b64decode(raw_username_info).decode('utf-8')
                if ':' in decoded_userinfo:
                    username, password = decoded_userinfo.split(':', 1)
                else:
                    username = decoded_userinfo
            except (base64.binascii.Error, UnicodeDecodeError):
                username = raw_username_info 
                if parsed_url.password:
                    password = parsed_url.password

        proxy_scheme = "socks5h" 
        
        if username and password is not None:
            safe_username = urllib.parse.quote(username)
            safe_password = urllib.parse.quote(password)
            proxy_address = f"{proxy_scheme}://{safe_username}:{safe_password}@{host}:{port}"
        elif username:
            safe_username = urllib.parse.quote(username)
            proxy_address = f"{proxy_scheme}://{safe_username}@{host}:{port}"
        else:
            proxy_address = f"{proxy_scheme}://{host}:{port}"
            
        return {"http": proxy_address, "https": proxy_address}

    except Exception as e:
        logging.error(f"解析代理失败 '{proxy_line}': {e}")
        return None

def load_proxies(filename=PROXY_FILE):
    """从文件中加载并解析代理列表"""
    proxies = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parsed = parse_proxy_url(line)
                    if parsed:
                        proxies.append(parsed)
        logging.info(f"从 {filename} 加载了 {len(proxies)} 个有效代理。")
    except FileNotFoundError:
        logging.error(f"代理文件 {filename} 未找到。")
    except Exception as e:
        logging.error(f"读取代理文件 {filename} 时发生错误: {e}")
    return proxies

def load_payload_data():
    """加载请求体所需的文件内容"""
    try:
        with open(FILE_PATHS["surge_config"], 'r', encoding='utf-8') as f:
            surge_config_content = f.read()
        with open(FILE_PATHS["clash_yaml"], 'r', encoding='utf-8') as f:
            clash_yaml_content = f.read()
        with open(FILE_PATHS["singbox_json"], 'r', encoding='utf-8') as f:
            singbox_json_content = f.read()
    except FileNotFoundError as e:
        logging.error(f"错误：找不到配置文件 {e.filename}。")
        return None
    except Exception as e:
        logging.error(f"读取配置文件时发生错误: {e}")
        return None

    return {
        "subscribe_template_surfboard": surge_config_content,
        "subscribe_template_stash": clash_yaml_content,
        "subscribe_template_surge": surge_config_content,
        "subscribe_template_singbox": singbox_json_content,
        "subscribe_template_clash": clash_yaml_content,
        "subscribe_template_clashmeta": clash_yaml_content
    }

def main():
    payload_data = load_payload_data()
    if not payload_data:
        sys.exit(1)

    proxies_list = load_proxies()
    if not proxies_list:
        logging.error("没有代理可供使用，无法发送请求。")
        sys.exit(1)

    success = False
    for i, proxy_config in enumerate(proxies_list):
        current_proxy_display = proxy_config['http'] if proxy_config else "无代理 (直接连接)"
        logging.info(f"尝试使用代理 {i+1}/{len(proxies_list)}: {current_proxy_display}")
        
        try:
            response = requests.post(
                URL,
                headers=HEADERS,
                data=json.dumps(payload_data),
                proxies=proxy_config,
                timeout=REQUEST_TIMEOUT
            )
            
            logging.info(f"请求发送状态码: {response.status_code} (使用代理: {current_proxy_display})")

            if response.ok:
                logging.info("请求成功!")
                try:
                    logging.info("响应内容 (JSON):")
                    logging.info(json.dumps(response.json(), indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    logging.info("响应内容 (Text):")
                    logging.info(response.text)
                
                success = True
                
                # --- 修改处: 发送 Telegram 成功通知，并传入成功的代理配置 ---
                success_message = (
                    f"✅ *任务成功*\n\n"
                    f"数据已成功发送到 CC云。\n\n"
                    f"*共有代理:*\n`{len(proxies_list)}`条。"
                )
                send_telegram_notification(
                    TELEGRAM_BOT_TOKEN, 
                    TELEGRAM_CHAT_ID, 
                    success_message, 
                    proxy_config=proxy_config  # 传入成功的代理
                )
                # --- 通知代码结束 ---

                break
            else:
                logging.warning(f"请求返回错误状态码: {response.status_code}。响应: {response.text[:200]}...")

        except requests.exceptions.Timeout:
            logging.warning(f"使用代理 {current_proxy_display} 请求超时 ({REQUEST_TIMEOUT}秒)。")
        except requests.exceptions.ProxyError as e:
            logging.warning(f"使用代理 {current_proxy_display}发生代理错误: {e}")
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"使用代理 {current_proxy_display}发生连接错误: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"使用代理 {current_proxy_display} 发送请求时发生一般错误: {e}")
        
        if i < len(proxies_list) - 1:
            logging.info("尝试下一个代理...")

    if success:
        logging.info("数据已成功发送。脚本执行完毕。")
    else:
        logging.error("所有代理尝试均失败，数据未能发送。")
        # --- 修改处: 发送失败通知，不使用代理以提高送达率 ---
        failure_message = (
            f"❌ *任务失败*\n\n"
            f"所有 {len(proxies_list)} 个代理均尝试失败，数据未能发送到 CC云。"
        )
        send_telegram_notification(
            TELEGRAM_BOT_TOKEN, 
            TELEGRAM_CHAT_ID, 
            failure_message, 
            proxy_config=None # 不传代理
        )
        # --- 通知代码结束 ---
        sys.exit(1)

if __name__ == "__main__":
    main()
