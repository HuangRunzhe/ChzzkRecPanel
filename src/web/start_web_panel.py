#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chzzk录制程序Web管理面板启动脚本
"""

import os
import sys
import argparse
import logging
from web_panel import RecorderWebPanel

def main():
    parser = argparse.ArgumentParser(description='Chzzk录制程序Web管理面板')
    parser.add_argument('--host', default='127.0.0.1', help='绑定主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='绑定端口 (默认: 8080)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', default='config_local.json', help='配置文件路径')
    parser.add_argument('--record-list', default='record_list.txt', help='频道列表文件路径')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # 检查文件是否存在
    if not os.path.exists(args.config):
        logger.error(f"配置文件不存在: {args.config}")
        sys.exit(1)
    
    if not os.path.exists(args.record_list):
        logger.warning(f"频道列表文件不存在: {args.record_list}")
        # 创建空的频道列表文件
        with open(args.record_list, 'w', encoding='utf-8') as f:
            pass
        logger.info(f"已创建空的频道列表文件: {args.record_list}")
    
    try:
        # 创建并启动Web面板
        panel = RecorderWebPanel(
            config_path=args.config,
            record_list_path=args.record_list
        )
        
        logger.info(f"启动Web管理面板: http://{args.host}:{args.port}")
        logger.info("按 Ctrl+C 停止服务")
        
        panel.run(host=args.host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
