#!/usr/bin/env python3
"""
系统监控脚本
定期检查Chzzk录制器状态，发现异常时发送通知
"""

import json
import logging
import os
import psutil
import requests
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SystemMonitor:
    def __init__(self, config_file: str = 'config.json'):
        """初始化系统监控"""
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.monitor_interval = 60  # 检查间隔（秒）
        self.last_check = {}
        
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def setup_logging(self):
        """设置日志"""
        # 创建logs目录
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_recorder_process(self) -> bool:
        """检查录制器进程是否运行"""
        try:
            # 查找Python进程中的recorder_main.py或multi_chzzk_recorder.py
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('recorder_main.py' in arg or 'multi_chzzk_recorder.py' in arg for arg in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 减少错误日志输出
            return False
            
        except Exception as e:
            # 减少错误日志输出
            return False
    
    def check_discord_bot_process(self) -> bool:
        """检查Discord bot进程是否运行"""
        if not self.config.get('use_discord_bot', False):
            return True  # 如果未启用Discord bot，则跳过检查
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('discord_bot.py' in arg for arg in cmdline):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 减少错误日志输出
            return False
            
        except Exception as e:
            # 减少错误日志输出
            return False
    
    def check_api_connectivity(self) -> bool:
        """检查API连接性"""
        try:
            # 测试Chzzk API连接
            response = requests.get(
                'https://api.chzzk.naver.com/service/v1/channels/7c992b6ba76eb14f84168df1da6ccdcb',
                timeout=5  # 减少超时时间
            )
            
            if response.status_code == 200:
                return True
            else:
                # 减少错误日志输出
                return False
                
        except Exception as e:
            # 减少错误日志输出
            return False
    
    def check_disk_space(self) -> bool:
        """检查磁盘空间"""
        try:
            save_dir = self.config.get('recording_save_root_dir', 'download/')
            if not os.path.exists(save_dir):
                self.logger.error(f"保存目录不存在: {save_dir}")
                return False
            
            disk_usage = psutil.disk_usage(save_dir)
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 5:  # 少于5GB空间
                self.logger.error(f"磁盘空间不足: 仅剩 {free_gb:.2f}GB")
                return False
            elif free_gb < 10:  # 少于10GB空间
                self.logger.warning(f"磁盘空间较少: 仅剩 {free_gb:.2f}GB")
            
            self.logger.info(f"磁盘空间正常: 剩余 {free_gb:.2f}GB")
            return True
            
        except Exception as e:
            self.logger.error(f"磁盘空间检查失败: {e}")
            return False
    
    def check_cookie_validity(self) -> bool:
        """检查cookie有效性"""
        try:
            nid_aut = self.config.get('nid_aut', '')
            nid_ses = self.config.get('nid_ses', '')
            
            if not nid_aut or not nid_ses:
                self.logger.error("Cookie配置缺失")
                return False
            
            # 测试API调用
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            cookies = {'NID_AUT': nid_aut, 'NID_SES': nid_ses}
            
            response = requests.get(
                'https://api.chzzk.naver.com/service/v1/channels/7c992b6ba76eb14f84168df1da6ccdcb',
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Cookie有效")
                return True
            else:
                self.logger.error(f"Cookie可能已过期: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cookie检查失败: {e}")
            return False
    
    def check_log_errors(self) -> List[str]:
        """检查日志文件中的错误"""
        errors = []
        log_files = ['logs/monitor.log', 'logs/auto_restart.log']
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # 检查最近1小时内的错误
                recent_errors = []
                for line in lines[-100:]:  # 只检查最后100行
                    if 'ERROR' in line or 'CRITICAL' in line:
                        recent_errors.append(line.strip())
                
                if recent_errors:
                    errors.extend(recent_errors[-5:])  # 最多5个最近错误
                    
            except Exception as e:
                self.logger.error(f"读取日志文件失败 {log_file}: {e}")
        
        return errors
    
    def send_notification(self, message: str, is_critical: bool = False):
        """发送通知"""
        try:
            # 这里可以集成Discord、邮件或其他通知方式
            self.logger.info(f"通知: {message}")
            
            # 如果启用了Discord bot，可以发送消息
            if self.config.get('use_discord_bot', False):
                self.send_discord_alert(message, is_critical)
                
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
    
    def send_discord_alert(self, message: str, is_critical: bool = False):
        """发送Discord警告"""
        # 这里需要集成到现有的Discord系统
        # 可以通过ZMQ发送消息到Discord bot
        pass
    
    def run_check(self):
        """运行一次完整检查"""
        # 减少日志输出
        # self.logger.info("开始系统检查...")
        
        checks = {
            'recorder_process': self.check_recorder_process(),
            'discord_bot_process': self.check_discord_bot_process(),
            'api_connectivity': self.check_api_connectivity(),
            'disk_space': self.check_disk_space(),
            'cookie_validity': self.check_cookie_validity()
        }
        
        failed_checks = [name for name, result in checks.items() if not result]
        
        # 只记录重要的错误
        if failed_checks:
            # 过滤掉不重要的检查项
            important_failures = [name for name in failed_checks if name in ['recorder_process', 'disk_space']]
            if important_failures:
                error_message = f"系统检查失败: {', '.join(important_failures)}"
                self.logger.error(error_message)
                self.send_notification(error_message, is_critical=True)
        
        # 减少日志错误检查
        # log_errors = self.check_log_errors()
        # if log_errors:
        #     error_message = f"发现日志错误:\n" + "\n".join(log_errors[-3:])
        #     self.logger.warning(error_message)
        #     self.send_notification(error_message, is_critical=False)
    
    def run_monitor(self):
        """运行持续监控"""
        self.logger.info("系统监控启动")
        
        while True:
            try:
                self.run_check()
                time.sleep(self.monitor_interval)
            except KeyboardInterrupt:
                self.logger.info("监控停止")
                break
            except Exception as e:
                self.logger.error(f"监控过程中出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续

def main():
    monitor = SystemMonitor()
    
    import argparse
    parser = argparse.ArgumentParser(description='Chzzk录制器系统监控')
    parser.add_argument('--once', action='store_true', help='只运行一次检查')
    args = parser.parse_args()
    
    if args.once:
        monitor.run_check()
    else:
        monitor.run_monitor()

if __name__ == "__main__":
    main()
