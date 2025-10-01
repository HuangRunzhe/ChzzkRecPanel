#!/usr/bin/env python3
"""
自动重启脚本
监控录制器进程，如果崩溃则自动重启
"""

import os
import sys
import time
import subprocess
import logging
import signal
import psutil
import json
import asyncio
import disnake as ds
from datetime import datetime, timedelta
import ssl
import schedule
import requests

# 禁用SSL验证 (Windows兼容)
import ssl
import os
import urllib3
import warnings

# 禁用SSL警告
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# 禁用urllib3警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# 设置代理（Clash默认端口）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

class AutoRestartManager:
    def __init__(self):
        self.setup_logging()
        self.recorder_process = None
        self.monitor_process = None
        self.restart_count = 0
        self.max_restarts = 10  # 最大重启次数
        self.restart_window = 3600  # 1小时内的重启窗口
        self.restart_times = []
        self.config = self.load_config()
        self.last_daily_summary = None
        
    def setup_logging(self):
        """设置日志"""
        # 创建logs目录
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/auto_restart.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """加载配置文件"""
        # 优先尝试加载本地配置文件
        config_files = ['config_local.json', 'config.json']
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"加载配置文件: {config_file}")
                    return config
            except FileNotFoundError:
                continue
            except Exception as e:
                self.logger.warning(f"加载配置文件 {config_file} 失败: {e}")
                continue
        
        self.logger.warning("未找到有效的配置文件，使用默认配置")
        return {}
    
    def send_discord_notification(self, title, description, color=0x00FF00):
        """发送Discord通知（使用requests库）"""
        try:
            notifications = self.config.get('notifications', {})
            if not notifications.get('use_discord_bot', False):
                self.logger.info("Discord通知已禁用")
                return
            
            token = notifications.get('discord_bot_token', '')
            channel_id = notifications.get('discord_channel_id', '')
            
            if not token or not channel_id or token == 'your_discord_bot_token_here' or channel_id == 'your_discord_channel_id_here':
                self.logger.warning("Discord配置无效，请检查discord_bot_token和discord_channel_id")
                return
            
            import requests
            
            # 创建embed消息
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "author": {
                    "name": "Chzzk Recorder",
                    "icon_url": "https://ssl.pstatic.net/static/nng/glive/icon/favicon.png"
                }
            }
            
            message_data = {
                "content": "",
                "embeds": [embed]
            }
            
            headers = {
                'Authorization': f'Bot {token}',
                'Content-Type': 'application/json'
            }
            
            # 发送到频道
            message_url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
            response = requests.post(message_url, headers=headers, json=message_data, timeout=10, verify=False)
            
            if response.status_code == 200:
                self.logger.info("Discord通知发送成功")
            else:
                self.logger.error(f"Discord通知发送失败: {response.status_code} - {response.text}")
            
        except Exception as e:
            self.logger.error(f"Discord通知出错: {e}")
    
    def send_telegram_notification(self, title, description):
        """发送Telegram通知"""
        try:
            notifications = self.config.get('notifications', {})
            if not notifications.get('use_telegram_bot', False):
                self.logger.info("Telegram通知已禁用")
                return
            
            bot_token = notifications.get('telegram_bot_token', '')
            chat_id = notifications.get('telegram_chat_id', '')
            
            if not bot_token or not chat_id or bot_token == 'your_telegram_bot_token_here' or chat_id == 'your_telegram_chat_id_here':
                self.logger.warning("Telegram配置无效，请检查telegram_bot_token和telegram_chat_id")
                return
            
            from telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier(bot_token, chat_id)
            
            # 格式化消息
            message = f"<b>{title}</b>\n\n{description}\n\n⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
            
            if notifier.send_message(message):
                self.logger.info("Telegram通知发送成功")
            else:
                self.logger.error("Telegram通知发送失败")
            
        except Exception as e:
            self.logger.error(f"Telegram通知出错: {e}")
    
    def send_notification(self, title, description, color=0x00FF00):
        """发送通知（同时发送到Discord和Telegram）"""
        # 避免emoji字符导致的编码问题
        safe_title = title.encode('ascii', 'ignore').decode('ascii') or "Notification"
        self.logger.info(f"发送通知: {safe_title}")
        self.send_discord_notification(title, description, color)
        self.send_telegram_notification(title, description)
    
    def get_daily_stats(self):
        """获取简化的每日统计数据"""
        try:
            response = requests.get("http://localhost:5000/api/daily-stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"获取统计数据失败: {e}")
            return None
    
    def send_daily_summary(self):
        """发送简化的每日总结"""
        try:
            stats = self.get_daily_stats()
            if not stats:
                return
            
            # 简化统计信息
            date = stats.get('date', 'Unknown')
            total_recordings = stats.get('total_recordings', 0)
            completed_recordings = stats.get('completed_recordings', 0)
            success_rate = stats.get('success_rate', 0)
            unique_streamers = stats.get('unique_streamers', 0)
            total_duration_hours = stats.get('total_duration_hours', 0)
            total_size_gb = stats.get('total_size_gb', 0)
            
            # 构建简化消息
            message = f"""📊 **{date} Daily Summary**

🎯 **Recordings**: {total_recordings} total, {completed_recordings} successful ({success_rate}%)
👥 **Streamers**: {unique_streamers} active
⏱️ **Duration**: {total_duration_hours:.1f} hours
💾 **Storage**: {total_size_gb:.1f} GB

---
📅 Generated: {datetime.now().strftime('%H:%M:%S')}"""
            
            # 发送通知
            self.send_discord_notification("📊 Daily Summary", message, 0x0099FF)
            self.send_telegram_notification("📊 Daily Summary", message)
            
            self.logger.info("每日总结发送成功")
            
        except Exception as e:
            self.logger.error(f"发送每日总结失败: {e}")
    
    def check_daily_summary(self):
        """检查是否需要发送每日总结"""
        now = datetime.now()
        current_date = now.date()
        
        # 如果今天还没有发送过总结，且是上午9点或下午6点
        if (self.last_daily_summary != current_date and 
            (now.hour == 9 or now.hour == 18)):
            self.send_daily_summary()
            self.last_daily_summary = current_date
    
    def start_recorder(self):
        """启动录制器"""
        try:
            self.logger.info("启动录制器...")
            # 优先使用新的录制端主程序
            if os.path.exists('recorder_main.py'):
                self.recorder_process = subprocess.Popen([
                    sys.executable, 'recorder_main.py'
                ], stdout=None, stderr=None)  # 直接输出到控制台
                self.logger.info("使用新的录制端主程序 (recorder_main.py)")
            else:
                # 回退到旧的录制器
                self.recorder_process = subprocess.Popen([
                    sys.executable, 'multi_chzzk_recorder.py'
                ], stdout=None, stderr=None)  # 直接输出到控制台
                self.logger.info("使用旧的录制器 (multi_chzzk_recorder.py)")
            
            self.logger.info(f"录制器已启动，PID: {self.recorder_process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动录制器失败: {e}")
            return False
    
    def start_monitor(self):
        """启动系统监控"""
        try:
            self.logger.info("启动系统监控...")
            self.monitor_process = subprocess.Popen([
                sys.executable, 'system_monitor.py'
            ], stdout=None, stderr=None)  # 直接输出到控制台
            
            self.logger.info(f"系统监控已启动，PID: {self.monitor_process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动系统监控失败: {e}")
            return False
    
    def is_recorder_running(self):
        """检查录制器是否运行"""
        if self.recorder_process is None:
            return False
        
        return self.recorder_process.poll() is None
    
    def is_monitor_running(self):
        """检查监控是否运行"""
        if self.monitor_process is None:
            return False
        
        return self.monitor_process.poll() is None
    
    def cleanup_old_restarts(self):
        """清理过期的重启记录"""
        now = time.time()
        self.restart_times = [t for t in self.restart_times if now - t < self.restart_window]
    
    def can_restart(self):
        """检查是否可以重启"""
        self.cleanup_old_restarts()
        return len(self.restart_times) < self.max_restarts
    
    def restart_recorder(self):
        """重启录制器"""
        if not self.can_restart():
            self.logger.error(f"达到最大重启次数限制 ({self.max_restarts}次/小时)")
            return False
        
        self.logger.info("重启录制器...")
        
        # 停止当前进程
        if self.recorder_process:
            try:
                self.recorder_process.terminate()
                self.recorder_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning("强制终止录制器进程")
                self.recorder_process.kill()
            except Exception as e:
                self.logger.error(f"停止录制器时出错: {e}")
        
        # 等待一段时间
        time.sleep(5)
        
        # 启动新进程
        if self.start_recorder():
            self.restart_count += 1
            self.restart_times.append(time.time())
            self.logger.info(f"录制器重启成功 (第{self.restart_count}次)")
            
            # 发送重启通知
            self.send_notification(
                title="🔄 Recorder Restarted",
                description=f"Recorder process has been automatically restarted after crash!\n\nRestart count: {self.restart_count}",
                color=0xFFA500
            )
            
            return True
        else:
            self.logger.error("录制器重启失败")
            return False
    
    def restart_monitor(self):
        """重启监控"""
        self.logger.info("重启系统监控...")
        
        # 停止当前进程
        if self.monitor_process:
            try:
                self.monitor_process.terminate()
                self.monitor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.warning("强制终止监控进程")
                self.monitor_process.kill()
            except Exception as e:
                self.logger.error(f"停止监控时出错: {e}")
        
        # 等待一段时间
        time.sleep(2)
        
        # 启动新进程
        return self.start_monitor()
    
    def check_and_restart(self):
        """检查并重启必要的进程"""
        # 检查录制器
        if not self.is_recorder_running():
            self.logger.warning("录制器进程已停止")
            if not self.restart_recorder():
                self.logger.error("无法重启录制器，请手动检查")
                return False
        
        # 检查监控
        if not self.is_monitor_running():
            self.logger.warning("监控进程已停止")
            if not self.restart_monitor():
                self.logger.error("无法重启监控")
        
        return True
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止...")
        
        if self.recorder_process:
            self.recorder_process.terminate()
        
        if self.monitor_process:
            self.monitor_process.terminate()
        
        sys.exit(0)
    
    def run(self):
        """运行自动重启管理器"""
        self.logger.info("自动重启管理器启动")
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 发送启动通知
        self.send_notification(
            title="🚀 Recorder System Started",
            description="Chzzk Recorder Auto-Restart Manager has started!\n\nThe system will automatically monitor recorder status and restart on crashes.",
            color=0x00FF00
        )
        
        # 启动初始进程
        if not self.start_recorder():
            self.logger.error("无法启动录制器")
            return
        
        if not self.start_monitor():
            self.logger.warning("无法启动监控，继续运行录制器")
        
        # 主循环
        check_interval = 120  # 120秒检查一次，减少CPU消耗
        last_check = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # 定期检查
                if current_time - last_check >= check_interval:
                    if not self.check_and_restart():
                        self.logger.error("检查失败，等待下次检查")
                    last_check = current_time
                
                # 检查每日总结
                self.check_daily_summary()
                
                time.sleep(5)  # 短暂休眠
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，正在停止...")
                break
            except Exception as e:
                self.logger.error(f"主循环中出错: {e}")
                time.sleep(10)
        
        # 清理
        if self.recorder_process:
            self.recorder_process.terminate()
        if self.monitor_process:
            self.monitor_process.terminate()
        
        self.logger.info("自动重启管理器已停止")

def main():
    manager = AutoRestartManager()
    manager.run()

if __name__ == "__main__":
    main()