#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 更新脚本
帮助用户更新 Chzzk Cookie
"""

import json
import os
import sys
from cookie_manager import CookieManager

def main():
    print("🍪 Chzzk Cookie 更新工具")
    print("=" * 50)
    print()
    
    cookie_manager = CookieManager()
    
    # 检查当前 Cookie 状态
    print("检查当前 Cookie 状态...")
    if cookie_manager.validate_cookies():
        print("✅ 当前 Cookie 仍然有效")
        choice = input("是否仍要更新？(y/N): ").lower()
        if choice != 'y':
            print("取消更新")
            return
    else:
        print("❌ 当前 Cookie 已失效")
    
    print()
    print("请按以下步骤获取新的 Cookie：")
    print("1. 打开浏览器，访问 https://chzzk.naver.com")
    print("2. 登录你的账号")
    print("3. 按 F12 打开开发者工具")
    print("4. 切换到 'Application' 或 '存储' 标签")
    print("5. 在左侧找到 'Cookies' -> 'https://chzzk.naver.com'")
    print("6. 找到 'NID_AUT' 和 'NID_SES' 的值")
    print()
    
    # 获取新的 Cookie 值
    print("请输入新的 Cookie 值：")
    nid_aut = input("NID_AUT: ").strip()
    nid_ses = input("NID_SES: ").strip()
    
    if not nid_aut or not nid_ses:
        print("❌ Cookie 值不能为空")
        return
    
    # 更新 Cookie
    print("\n正在更新 Cookie...")
    if cookie_manager.update_cookies(nid_aut, nid_ses):
        print("✅ Cookie 更新成功！")
        print("录制器将在下次检查时使用新的 Cookie")
    else:
        print("❌ Cookie 更新失败")
        print("请检查 Cookie 值是否正确")

if __name__ == "__main__":
    main()
