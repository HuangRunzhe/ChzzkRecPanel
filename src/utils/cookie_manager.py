#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 管理器
自动检测和更新 Chzzk Cookie
"""

import json
import logging
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class CookieManager:
    def __init__(self, config_path: str = "config_local.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.last_check_time = None
        self.check_interval = 300  # 5分钟检查一次
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Config saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def validate_cookies(self) -> bool:
        """验证当前 Cookie 是否有效"""
        try:
            nid_aut = self.config.get('recording', {}).get('nid_aut', '')
            nid_ses = self.config.get('recording', {}).get('nid_ses', '')
            
            # 检查是否是占位符
            if (not nid_aut or not nid_ses or 
                nid_aut == 'YOUR_NID_AUT_HERE' or 
                nid_ses == 'YOUR_NID_SES_HERE'):
                logger.error("Cookie configuration missing or placeholder")
                return False
            
            # 测试 API 调用
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            cookies = {'NID_AUT': nid_aut, 'NID_SES': nid_ses}
            
            # 使用一个简单的 API 端点测试
            response = requests.get(
                'https://api.chzzk.naver.com/service/v1/channels/7c992b6ba76eb14f84168df1da6ccdcb',
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Cookie validation successful")
                return True
            elif response.status_code == 500:
                logger.warning("Cookie may have expired (HTTP 500)")
                return False
            else:
                logger.warning(f"Cookie validation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Cookie validation failed: {e}")
            return False
    
    def should_check_cookies(self) -> bool:
        """判断是否需要检查 Cookie"""
        if self.last_check_time is None:
            return True
        
        time_since_last_check = time.time() - self.last_check_time
        return time_since_last_check >= self.check_interval
    
    def check_and_update_cookies(self) -> bool:
        """检查并更新 Cookie（如果需要）"""
        if not self.should_check_cookies():
            return True
        
        self.last_check_time = time.time()
        
        if self.validate_cookies():
            logger.info("Cookie is still valid")
            return True
        else:
            logger.warning("Cookie has expired, manual update required")
            self.notify_cookie_expired()
            return False
    
    def notify_cookie_expired(self):
        """Notify that Cookie has expired"""
        logger.error("=" * 60)
        logger.error("🚨 COOKIE EXPIRED!")
        logger.error("=" * 60)
        logger.error("Please follow these steps to update your Cookie:")
        logger.error("")
        logger.error("1. Open your browser and visit https://chzzk.naver.com")
        logger.error("2. Log in to your account")
        logger.error("3. Press F12 to open Developer Tools")
        logger.error("4. Switch to 'Application' or 'Storage' tab")
        logger.error("5. Find 'Cookies' -> 'https://chzzk.naver.com' on the left")
        logger.error("6. Copy the values of 'NID_AUT' and 'NID_SES'")
        logger.error("7. Update the corresponding values in config_local.json file")
        logger.error("")
        logger.error("Or run: python update_cookies.py")
        logger.error("=" * 60)
    
    def get_cookies(self) -> Tuple[str, str]:
        """获取当前的 Cookie 值"""
        nid_aut = self.config.get('recording', {}).get('nid_aut', '')
        nid_ses = self.config.get('recording', {}).get('nid_ses', '')
        return nid_aut, nid_ses
    
    def update_cookies(self, nid_aut: str, nid_ses: str) -> bool:
        """更新 Cookie 值"""
        try:
            if 'recording' not in self.config:
                self.config['recording'] = {}
            
            self.config['recording']['nid_aut'] = nid_aut
            self.config['recording']['nid_ses'] = nid_ses
            
            self.save_config()
            
            # 验证新 Cookie
            if self.validate_cookies():
                logger.info("Cookie updated successfully and validated")
                return True
            else:
                logger.error("Cookie update failed, validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update Cookie: {e}")
            return False

def main():
    """Main function - for testing Cookie manager"""
    cookie_manager = CookieManager()
    
    print("🍪 Cookie Manager Test")
    print("=" * 40)
    
    # Check current Cookie
    print("Checking current Cookie...")
    if cookie_manager.validate_cookies():
        print("✅ Cookie is valid")
    else:
        print("❌ Cookie is invalid")
        cookie_manager.notify_cookie_expired()

if __name__ == "__main__":
    main()
