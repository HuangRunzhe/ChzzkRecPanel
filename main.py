#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chzzk Recorder Launcher
Main entry point for the Chzzk recording system
"""

import sys
import os
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    parser = argparse.ArgumentParser(description='Chzzk Recorder')
    parser.add_argument('--mode', choices=['recorder', 'web'], default='recorder',
                       help='Run mode: recorder or web panel')
    parser.add_argument('--config', default='src/config/config_local.json',
                       help='Configuration file path')
    parser.add_argument('--host', default='127.0.0.1', help='Web panel host')
    parser.add_argument('--port', type=int, default=8080, help='Web panel port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.mode == 'recorder':
        from src.core.recorder_main import main as recorder_main
        # 设置配置文件路径
        os.environ['CONFIG_PATH'] = args.config
        recorder_main()
    elif args.mode == 'web':
        from src.web.start_web_panel import main as web_main
        sys.argv = ['start_web_panel.py', '--host', args.host, '--port', str(args.port)]
        if args.debug:
            sys.argv.append('--debug')
        web_main()

if __name__ == '__main__':
    main()
