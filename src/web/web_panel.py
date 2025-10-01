#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chzzk录制程序 Web 管理面板
提供本地Web界面来管理录制配置和监控录制状态
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecorderWebPanel:
    def __init__(self, config_path="config_local.json", record_list_path="record_list.txt"):
        self.config_path = config_path
        self.record_list_path = record_list_path
        self.config = self.load_config()
        self.recorder_processes = {}  # 存储录制进程信息
        self.is_running = False
        
        # 创建Flask应用
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        
        # 配置CORS
        CORS(self.app)
        
        # 配置SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 注册路由
        self.register_routes()
        
        # 启动状态监控线程
        self.start_status_monitor()
    
    def load_config(self):
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
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def load_channel_list(self):
        """加载频道列表"""
        try:
            if not os.path.exists(self.record_list_path):
                return []
            
            with open(self.record_list_path, 'r', encoding='utf-8') as f:
                channels = []
                for line in f:
                    channel_id = line.strip()
                    if channel_id:
                        # 尝试获取频道信息
                        channel_info = self.get_channel_info(channel_id)
                        channels.append({
                            'channel_id': channel_id,
                            'channel_name': channel_info.get('channelName', f'Channel_{channel_id[:8]}'),
                            'channel_image': channel_info.get('channelImageUrl', ''),
                            'is_live': channel_info.get('isLive', False),
                            'live_title': channel_info.get('liveTitle', ''),
                            'viewer_count': channel_info.get('viewerCount', 0)
                        })
                return channels
        except Exception as e:
            logger.error(f"Failed to load channel list: {e}")
            return []
    
    def save_channel_list(self, channels):
        """保存频道列表"""
        try:
            with open(self.record_list_path, 'w', encoding='utf-8') as f:
                for channel in channels:
                    f.write(f"{channel['channel_id']}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to save channel list: {e}")
            return False
    
    def get_channel_info(self, channel_id):
        """获取频道信息"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                f'https://api.chzzk.naver.com/service/v1/channels/{channel_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('content'):
                    content = data['content']
                    return {
                        'channelName': content.get('channelName', ''),
                        'channelImageUrl': content.get('channelImageUrl', ''),
                        'isLive': content.get('openLive', False),
                        'liveTitle': content.get('liveTitle', ''),
                        'viewerCount': content.get('concurrentUserCount', 0)
                    }
        except Exception as e:
            logger.warning(f"Failed to get channel info for {channel_id}: {e}")
        
        return {}
    
    def register_routes(self):
        """注册路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def get_status():
            """获取系统状态"""
            try:
                channels = self.load_channel_list()
                live_channels = [ch for ch in channels if ch['is_live']]
                
                return jsonify({
                    'status': 'running',
                    'total_channels': len(channels),
                    'live_channels': len(live_channels),
                    'recording_channels': len(self.recorder_processes),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels')
        def get_channels():
            """获取频道列表"""
            try:
                channels = self.load_channel_list()
                return jsonify(channels)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels', methods=['POST'])
        def add_channel():
            """添加频道"""
            try:
                data = request.get_json()
                channel_id = data.get('channel_id', '').strip()
                
                if not channel_id:
                    return jsonify({'error': 'Channel ID is required'}), 400
                
                # 验证频道是否存在
                channel_info = self.get_channel_info(channel_id)
                if not channel_info.get('channelName'):
                    return jsonify({'error': 'Invalid channel ID'}), 400
                
                # 加载现有频道列表
                channels = self.load_channel_list()
                channel_ids = [ch['channel_id'] for ch in channels]
                
                if channel_id in channel_ids:
                    return jsonify({'error': 'Channel already exists'}), 400
                
                # 添加新频道
                new_channel = {
                    'channel_id': channel_id,
                    'channel_name': channel_info.get('channelName', f'Channel_{channel_id[:8]}'),
                    'channel_image': channel_info.get('channelImageUrl', ''),
                    'is_live': channel_info.get('isLive', False),
                    'live_title': channel_info.get('liveTitle', ''),
                    'viewer_count': channel_info.get('viewerCount', 0)
                }
                
                channels.append(new_channel)
                
                if self.save_channel_list(channels):
                    return jsonify({'success': True, 'channel': new_channel})
                else:
                    return jsonify({'error': 'Failed to save channel list'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels/<channel_id>', methods=['DELETE'])
        def delete_channel(channel_id):
            """删除频道"""
            try:
                channels = self.load_channel_list()
                channels = [ch for ch in channels if ch['channel_id'] != channel_id]
                
                if self.save_channel_list(channels):
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Failed to save channel list'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def get_config():
            """获取配置"""
            try:
                return jsonify(self.config)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['PUT'])
        def update_config():
            """更新配置"""
            try:
                data = request.get_json()
                
                # 更新配置
                for section, values in data.items():
                    if section in self.config:
                        self.config[section].update(values)
                    else:
                        self.config[section] = values
                
                if self.save_config():
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Failed to save config'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/status')
        def get_recording_status():
            """获取录制状态"""
            try:
                return jsonify({
                    'recording_channels': list(self.recorder_processes.keys()),
                    'processes': self.recorder_processes
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/start/<channel_id>', methods=['POST'])
        def start_recording(channel_id):
            """开始录制"""
            try:
                # 这里需要与主录制程序通信
                # 暂时返回模拟响应
                return jsonify({'success': True, 'message': 'Recording started'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/stop/<channel_id>', methods=['POST'])
        def stop_recording(channel_id):
            """停止录制"""
            try:
                # 这里需要与主录制程序通信
                # 暂时返回模拟响应
                return jsonify({'success': True, 'message': 'Recording stopped'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        def get_logs():
            """获取日志"""
            try:
                log_file = os.path.join(os.path.dirname(__file__), 'logs', 'recorder.log')
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 返回最后100行
                        return jsonify({'logs': lines[-100:]})
                else:
                    return jsonify({'logs': []})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start_status_monitor(self):
        """启动状态监控线程"""
        def monitor():
            while self.is_running:
                try:
                    # 更新频道状态
                    channels = self.load_channel_list()
                    updated_channels = []
                    
                    for channel in channels:
                        channel_info = self.get_channel_info(channel['channel_id'])
                        channel.update({
                            'is_live': channel_info.get('isLive', False),
                            'live_title': channel_info.get('liveTitle', ''),
                            'viewer_count': channel_info.get('viewerCount', 0)
                        })
                        updated_channels.append(channel)
                    
                    # 通过WebSocket发送更新
                    self.socketio.emit('status_update', {
                        'channels': updated_channels,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    time.sleep(30)  # 每30秒更新一次
                    
                except Exception as e:
                    logger.error(f"Status monitor error: {e}")
                    time.sleep(10)
        
        self.is_running = True
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def run(self, host='127.0.0.1', port=8080, debug=False):
        """运行Web面板"""
        logger.info(f"Starting Recorder Web Panel on http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

def main():
    """主函数"""
    panel = RecorderWebPanel()
    panel.run(debug=True)

if __name__ == '__main__':
    main()
