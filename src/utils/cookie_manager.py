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
                logger.error("Cookie配置缺失或为占位符")
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
                logger.info("Cookie验证成功")
                return True
            elif response.status_code == 500:
                logger.warning("Cookie可能已过期 (HTTP 500)")
                return False
            else:
                logger.warning(f"Cookie验证失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Cookie验证失败: {e}")
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
            logger.info("Cookie仍然有效")
            return True
        else:
            logger.warning("Cookie已失效，需要手动更新")
            self.notify_cookie_expired()
            return False
    
    def notify_cookie_expired(self):
        """通知 Cookie 已过期"""
        logger.error("=" * 60)
        logger.error("🚨 COOKIE 已过期！")
        logger.error("=" * 60)
        logger.error("请按以下步骤更新 Cookie：")
        logger.error("")
        logger.error("1. 打开浏览器，访问 https://chzzk.naver.com")
        logger.error("2. 登录你的账号")
        logger.error("3. 按 F12 打开开发者工具")
        logger.error("4. 切换到 'Application' 或 '存储' 标签")
        logger.error("5. 在左侧找到 'Cookies' -> 'https://chzzk.naver.com'")
        logger.error("6. 复制 'NID_AUT' 和 'NID_SES' 的值")
        logger.error("7. 更新 config_local.json 文件中的对应值")
        logger.error("")
        logger.error("或者运行: python update_cookies.py")
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
                logger.info("Cookie更新成功并验证通过")
                return True
            else:
                logger.error("Cookie更新失败，验证不通过")
                return False
                
        except Exception as e:
            logger.error(f"更新Cookie失败: {e}")
            return False

def main():
    """主函数 - 用于测试 Cookie 管理器"""
    cookie_manager = CookieManager()
    
    print("🍪 Cookie 管理器测试")
    print("=" * 40)
    
    # 检查当前 Cookie
    print("检查当前 Cookie...")
    if cookie_manager.validate_cookies():
        print("✅ Cookie 有效")
    else:
        print("❌ Cookie 无效")
        cookie_manager.notify_cookie_expired()

if __name__ == "__main__":
    main()
