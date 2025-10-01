#!/usr/bin/env python3
"""
英语通知发送脚本
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """加载配置"""
    try:
        with open('config_local.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return None

def get_english_message(channel_name: str, live_title: str, live_url: str):
    """获取英语消息"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""🎥 Recording Started

Channel: {channel_name}
Title: {live_title}
Viewers: 0

🔗 Watch Live: {live_url}

---
📅 {current_time}"""
    
    return message

def send_telegram_english(message: str, image_path: str = None):
    """发送Telegram通知（英语版）"""
    try:
        config = load_config()
        if not config:
            return False
        
        bot_token = config['notifications']['telegram_bot_token']
        chat_id = config['notifications']['telegram_chat_id']
        
        # 使用代理
        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
        timeout = 15
        
        if image_path and os.path.exists(image_path):
            # 发送带图片的消息
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=data, timeout=timeout, verify=False, proxies=proxies)
        else:
            # 发送纯文本消息
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=data, timeout=timeout, verify=False, proxies=proxies)
        
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent successfully")
            return True
        else:
            logger.error(f"❌ Telegram notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Telegram notification error: {e}")
        return False

def send_discord_english(message: str, image_path: str = None):
    """发送Discord通知（英语版）"""
    try:
        config = load_config()
        if not config:
            return False
        
        bot_token = config['notifications']['discord_bot_token']
        channel_id = config['notifications']['discord_channel_id']
        
        # 使用代理
        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
        timeout = 15
        
        # 创建Discord embed
        embed = {
            "title": "🎥 Recording Started",
            "description": message,
            "color": 0x00FF00,  # 绿色
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Chzzk Recorder"
            }
        }
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }
        
        if image_path and os.path.exists(image_path):
            # 先发送embed消息
            payload = {"embeds": [embed]}
            response = requests.post(url, headers=headers, json=payload, timeout=timeout, verify=False, proxies=proxies)
            
            if response.status_code == 200:
                # 再发送图片 - 使用正确的multipart格式
                with open(image_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(image_path), f, 'image/jpeg')
                    }
                    data = {
                        'content': '📸 Live Screenshot'
                    }
                    # 移除Content-Type头，让requests自动设置
                    headers_without_content_type = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
                    response = requests.post(url, headers=headers_without_content_type, files=files, data=data, timeout=timeout, verify=False, proxies=proxies)
                
                if response.status_code == 200:
                    logger.info("✅ Discord notification sent successfully (with screenshot)")
                    return True
                else:
                    logger.warning(f"Discord image upload failed: {response.status_code} - {response.text}")
                    return True  # 消息已发送，图片失败不算完全失败
            else:
                logger.error(f"❌ Discord notification failed: {response.status_code} - {response.text}")
                return False
        else:
            # 发送纯文本消息
            payload = {"embeds": [embed]}
            response = requests.post(url, headers=headers, json=payload, timeout=timeout, verify=False, proxies=proxies)
            
            if response.status_code == 200:
                logger.info("✅ Discord notification sent successfully")
                return True
            else:
                logger.error(f"❌ Discord notification failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Discord notification error: {e}")
        return False

def main():
    """主函数"""
    print("📢 English Notification Sender")
    print("=" * 40)
    
    # 频道信息
    channel_id = "7c992b6ba76eb14f84168df1da6ccdcb"
    channel_name = "Channel_7c992b6b"
    live_title = "Live Streaming Now..."
    live_url = f"https://chzzk.naver.com/live/{channel_id}"
    
    print(f"📺 Channel: {channel_name}")
    print(f"🔗 Live URL: {live_url}")
    print()
    
    # 检查是否有截图文件
    screenshot_dir = "download/screenshots"
    screenshot_files = []
    if os.path.exists(screenshot_dir):
        for file in os.listdir(screenshot_dir):
            if file.endswith('.jpg') and channel_id in file:
                screenshot_files.append(os.path.join(screenshot_dir, file))
    
    if screenshot_files:
        # 使用最新的截图
        latest_screenshot = max(screenshot_files, key=os.path.getctime)
        print(f"📸 Found screenshot: {latest_screenshot}")
    else:
        latest_screenshot = None
        print("⚠️ No screenshot found")
    
    print()
    
    # 获取英语消息
    message = get_english_message(channel_name, live_title, live_url)
    
    # 发送通知
    print("📱 Sending Telegram notification...")
    telegram_success = send_telegram_english(message, latest_screenshot)
    
    print("💬 Sending Discord notification...")
    discord_success = send_discord_english(message, latest_screenshot)
    
    print()
    print("=" * 40)
    if telegram_success and discord_success:
        print("✅ All notifications sent successfully!")
    elif telegram_success or discord_success:
        print("⚠️ Partial notifications sent successfully")
    else:
        print("❌ Notification sending failed")
    print("=" * 40)

if __name__ == "__main__":
    main()
