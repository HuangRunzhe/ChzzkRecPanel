#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import ssl
from datetime import datetime

class TelegramNotifier:
    """Telegram通知发送器"""
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # 设置代理（如果需要）
        self.setup_proxy()
        
    def setup_proxy(self):
        """设置代理"""
        # 设置代理（Clash默认端口）
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
        os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
        os.environ['http_proxy'] = 'http://127.0.0.1:7890'
        os.environ['https_proxy'] = 'http://127.0.0.1:7890'
        
        # 禁用SSL验证
        ssl._create_default_https_context = ssl._create_unverified_context
    
    def send_message(self, text, parse_mode=None, disable_web_page_preview=True):
        """发送文本消息"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": disable_web_page_preview
            }
            
            # 只有在指定了解析模式时才添加
            if parse_mode:
                data["parse_mode"] = parse_mode
            
            response = requests.post(url, json=data, timeout=10, verify=False)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Telegram发送失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Telegram发送出错: {e}")
            return False
    
    def send_photo(self, photo_path, caption="", parse_mode="HTML"):
        """发送图片消息"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            # 检查是否是本地文件路径
            if os.path.exists(photo_path):
                # 发送本地文件
                with open(photo_path, 'rb') as photo_file:
                    files = {'photo': photo_file}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": parse_mode
                    }
                    response = requests.post(url, files=files, data=data, timeout=30, verify=False)
            else:
                # 发送URL
                data = {
                    "chat_id": self.chat_id,
                    "photo": photo_path,
                    "caption": caption,
                    "parse_mode": parse_mode
                }
                response = requests.post(url, json=data, timeout=10, verify=False)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Telegram发送图片失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Telegram发送图片出错: {e}")
            return False
    
    def send_recording_started(self, username, live_title, thumbnail_url, save_path):
        """发送录制开始通知"""
        text = f"""🔴 <b>Live Recording Started</b>

👤 <b>Streamer:</b> {username}
📺 <b>Title:</b> {live_title}
💾 <b>Save Path:</b> <code>{save_path}</code>
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Recording in progress...</i>"""
        
        if thumbnail_url:
            return self.send_photo(thumbnail_url, text)
        else:
            return self.send_message(text)
    
    def send_recording_ended(self, username, file_path, file_size):
        """发送录制结束通知"""
        text = f"""⏹️ <b>Live Recording Ended</b>

👤 <b>Streamer:</b> {username}
💾 <b>File Path:</b> <code>{file_path}</code>
📊 <b>File Size:</b> {file_size}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Recording completed successfully!</i>"""
        
        return self.send_message(text)
    
    def send_recording_ended_converting(self, username, file_path, file_size):
        """发送录制结束通知（转码中）"""
        text = f"""⏹️ <b>Live Recording Ended</b>

👤 <b>Streamer:</b> {username}
💾 <b>File Path:</b> <code>{file_path}</code>
📊 <b>File Size:</b> {file_size}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔄 <b>Converting to MP4...</b>

<i>Recording completed, conversion in progress!</i>"""
        
        return self.send_message(text)
    
    def send_conversion_completed(self, username, mp4_path, mp4_size, cover_image=None, thumbnail_image=None):
        """发送转码完成通知"""
        text = f"""✅ <b>Conversion Completed</b>

👤 <b>Streamer:</b> {username}
📁 <b>MP4 File:</b> <code>{mp4_path}</code>
📊 <b>File Size:</b> {mp4_size}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        if cover_image and thumbnail_image:
            text += "\n🖼️ <b>Images:</b> Cover + Thumbnail generated"
        elif cover_image or thumbnail_image:
            text += "\n🖼️ <b>Images:</b> Generated"
        
        text += "\n\n<i>Recording converted to MP4 successfully!</i>"
        
        # 优先发送封面图，如果没有则发送缩略图
        image_to_send = cover_image if cover_image and os.path.exists(cover_image) else thumbnail_image
        
        if image_to_send and os.path.exists(image_to_send):
            return self.send_photo(image_to_send, text)
        else:
            return self.send_message(text)
    
    def send_conversion_failed(self, username, ts_path):
        """发送转码失败通知"""
        text = f"""❌ <b>Conversion Failed</b>

👤 <b>Streamer:</b> {username}
📁 <b>TS File:</b> <code>{ts_path}</code>
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Failed to convert recording to MP4!</i>"""
        
        return self.send_message(text)
    
    def send_system_startup(self):
        """发送系统启动通知"""
        text = f"""🚀 <b>Recorder System Started</b>

Chzzk Recorder Auto-Restart Manager has started!

The system will automatically monitor recorder status and restart on crashes.

⏰ <b>Start Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>System is now running...</i>"""
        
        return self.send_message(text)
    
    def send_system_restart(self, restart_count):
        """发送系统重启通知"""
        text = f"""🔄 <b>Recorder Restarted</b>

Recorder process has been automatically restarted after crash!

🔄 <b>Restart Count:</b> {restart_count}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>System recovered successfully!</i>"""
        
        return self.send_message(text)
    
    def test_connection(self):
        """测试连接"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10, verify=False)
            
            if response.status_code == 200:
                bot_info = response.json()['result']
                print(f"✅ Telegram Bot连接成功: {bot_info['first_name']} (@{bot_info['username']})")
                return True
            else:
                print(f"❌ Telegram Bot连接失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram Bot连接出错: {e}")
            return False

def test_telegram_notification():
    """测试Telegram通知"""
    print("开始测试Telegram通知...")
    
    # 从config.json读取配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        bot_token = config.get('telegram_bot_token', '')
        chat_id = config.get('telegram_chat_id', '')
        
        if not bot_token or not chat_id:
            print("❌ 请在config.json中设置telegram_bot_token和telegram_chat_id")
            return
        
        notifier = TelegramNotifier(bot_token, chat_id)
        
        # 测试连接
        if notifier.test_connection():
            # 发送测试消息
            test_message = f"""🧪 <b>Telegram Test Message</b>

This is a test notification from Chzzk Recorder!

⏰ <b>Test Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>If you receive this message, Telegram integration is working correctly!</i>"""
            
            if notifier.send_message(test_message):
                print("✅ 测试消息发送成功！")
                print("请检查你的Telegram群组，应该会收到一条测试消息。")
            else:
                print("❌ 测试消息发送失败")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_telegram_notification()
