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
            logger.info(f"Loading channel list from: {self.record_list_path}")
            logger.info(f"File exists: {os.path.exists(self.record_list_path)}")
            
            if not os.path.exists(self.record_list_path):
                logger.warning(f"Channel list file does not exist: {self.record_list_path}")
                return []
            
            with open(self.record_list_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"File content: {repr(content)}")
                
                channels = []
                for line in content.strip().split('\n'):
                    channel_id = line.strip()
                    if channel_id:
                        logger.info(f"Found channel ID: {channel_id}")
                        # 获取频道信息以检查直播状态
                        channel_info = self.get_channel_info(channel_id)
                        channels.append({
                            'channel_id': channel_id,
                            'channel_name': channel_info.get('channelName', f'Channel_{channel_id[:8]}'),
                            'channel_image': channel_info.get('channelImageUrl', ''),
                            'is_live': channel_info.get('isLive', False),
                            'live_title': channel_info.get('liveTitle', ''),
                            'viewer_count': channel_info.get('viewerCount', 0)
                        })
            
            logger.info(f"Loaded {len(channels)} channels")
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
            
            logger.info(f"API response for {channel_id}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API data: {data}")
                if data.get('content'):
                    content = data['content']
                    result = {
                        'channelName': content.get('channelName', ''),
                        'channelImageUrl': content.get('channelImageUrl', ''),
                        'isLive': content.get('openLive', False) or content.get('channelType') == 'STREAMING',
                        'liveTitle': content.get('liveTitle', ''),
                        'viewerCount': content.get('concurrentUserCount', 0)
                    }
                    logger.info(f"Parsed channel info: {result}")
                    return result
                else:
                    logger.warning(f"No content in API response for {channel_id}")
            else:
                logger.warning(f"API request failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to get channel info for {channel_id}: {e}")
        
        return {}
    
    def check_recording_status(self, channel_id):
        """检查频道是否正在录制"""
        try:
            # 获取配置中的录制目录
            config_path = os.path.join(os.getcwd(), 'src', 'config', 'config_local.json')
            recording_dir = 'download'  # 默认目录
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        recording_dir = config.get('recording', {}).get('recording_save_root_dir', 'download')
                except Exception as e:
                    logger.warning(f"Failed to read config for recording directory: {e}")
            
            recording_path = os.path.join(os.getcwd(), recording_dir)
            logger.info(f"Checking recording status for channel {channel_id} in: {recording_path}")
            
            if os.path.exists(recording_path):
                # 递归搜索所有子目录
                for root, dirs, files in os.walk(recording_path):
                    for filename in files:
                        if filename.endswith('.ts'):
                            file_path = os.path.join(root, filename)
                            # 检查文件是否在最近5分钟内被修改（表示正在录制）
                            try:
                                mtime = os.path.getmtime(file_path)
                                time_diff = time.time() - mtime
                                logger.debug(f"Checking file: {filename}, modified {time_diff:.1f}s ago")
                                
                                if time_diff < 300:  # 5分钟内
                                    # 检查文件名是否包含频道ID（完整ID或前8位）
                                    channel_id_short = channel_id[:8]
                                    
                                    # 多种匹配模式
                                    if (channel_id in filename or 
                                        channel_id_short in filename or
                                        f"Channel_{channel_id_short}" in filename or
                                        filename.startswith(f"Channel_{channel_id_short}")):
                                        logger.info(f"Found active recording file: {file_path} (modified: {time_diff:.1f}s ago)")
                                        return True
                                    else:
                                        # 检查是否在主播昵称文件夹中
                                        parent_dir = os.path.basename(os.path.dirname(file_path))
                                        if (channel_id in parent_dir or 
                                            channel_id_short in parent_dir or
                                            f"Channel_{channel_id_short}" in parent_dir):
                                            logger.info(f"Found active recording file in channel folder: {file_path} (modified: {time_diff:.1f}s ago)")
                                            return True
                                        logger.debug(f"File {filename} doesn't match channel {channel_id} (short: {channel_id_short})")
                                else:
                                    logger.debug(f"File {filename} too old: {time_diff:.1f}s ago")
                            except Exception as e:
                                logger.warning(f"Failed to check file {file_path}: {e}")
                                continue
            
            logger.info(f"No active recording found for channel {channel_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to check recording status for {channel_id}: {e}")
            return False
    
    def scan_recording_history(self, recording_path):
        """扫描录制历史记录"""
        try:
            history = []
            
            if not os.path.exists(recording_path):
                logger.warning(f"Recording path does not exist: {recording_path}")
                return history
            
            # 递归扫描所有录制文件
            for root, dirs, files in os.walk(recording_path):
                for filename in files:
                    if filename.endswith(('.ts', '.mp4')):
                        file_path = os.path.join(root, filename)
                        try:
                            # 获取文件信息
                            stat = os.stat(file_path)
                            file_size = stat.st_size
                            created_time = stat.st_ctime
                            modified_time = stat.st_mtime
                            
                            # 解析文件名获取信息
                            file_info = self.parse_recording_filename(filename)
                            
                            # 查找对应的封面文件
                            cover_path = self.find_cover_file(file_path)
                            
                            # 查找对应的缩略图文件
                            thumbnail_path = self.find_thumbnail_file(file_path)
                            
                            recording_info = {
                                'filename': filename,
                                'file_path': file_path,
                                'relative_path': os.path.relpath(file_path, recording_path),
                                'file_size': file_size,
                                'file_size_mb': round(file_size / (1024 * 1024), 2),
                                'created_time': datetime.fromtimestamp(created_time).isoformat(),
                                'modified_time': datetime.fromtimestamp(modified_time).isoformat(),
                                'created_date': datetime.fromtimestamp(created_time).strftime('%Y-%m-%d'),
                                'created_time_str': datetime.fromtimestamp(created_time).strftime('%H:%M:%S'),
                                'channel_id': file_info.get('channel_id', ''),
                                'channel_name': file_info.get('channel_name', 'Unknown'),
                                'stream_title': file_info.get('stream_title', ''),
                                'stream_date': file_info.get('stream_date', ''),
                                'file_type': 'video' if filename.endswith('.mp4') else 'stream',
                                'cover_path': cover_path,
                                'thumbnail_path': thumbnail_path,
                                'duration': self.get_video_duration(file_path) if filename.endswith('.mp4') else None
                            }
                            
                            history.append(recording_info)
                            
                        except Exception as e:
                            logger.warning(f"Failed to process file {file_path}: {e}")
                            continue
            
            # 按创建时间倒序排列（最新的在前）
            history.sort(key=lambda x: x['created_time'], reverse=True)
            
            logger.info(f"Found {len(history)} recording files")
            return history
            
        except Exception as e:
            logger.error(f"Failed to scan recording history: {e}")
            return []
    
    def parse_recording_filename(self, filename):
        """解析录制文件名获取信息"""
        try:
            # 移除文件扩展名
            name_without_ext = os.path.splitext(filename)[0]
            
            # 尝试解析不同的文件名格式
            # 格式1: 主播名_20251001_225117_直播标题.ts
            # 格式2: 主播名_20251001_225117.ts
            # 格式3: local_时间戳_频道ID前8位.ts
            
            parts = name_without_ext.split('_')
            
            if len(parts) >= 3:
                # 检查是否是时间戳格式 (local_时间戳_频道ID)
                if parts[0] == 'local' and len(parts) >= 3:
                    timestamp = int(parts[1])
                    channel_id_short = parts[2]
                    return {
                        'channel_id': channel_id_short,
                        'channel_name': f'Channel_{channel_id_short}',
                        'stream_title': '',
                        'stream_date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    }
                
                # 尝试解析标准格式
                channel_name = parts[0]
                if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 8:
                    stream_date = parts[1]
                    stream_title = '_'.join(parts[3:]) if len(parts) > 3 else ''
                    
                    return {
                        'channel_id': '',
                        'channel_name': channel_name,
                        'stream_title': stream_title,
                        'stream_date': f"{stream_date[:4]}-{stream_date[4:6]}-{stream_date[6:8]}"
                    }
            
            # 如果无法解析，返回基本信息
            return {
                'channel_id': '',
                'channel_name': 'Unknown',
                'stream_title': '',
                'stream_date': ''
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse filename {filename}: {e}")
            return {
                'channel_id': '',
                'channel_name': 'Unknown',
                'stream_title': '',
                'stream_date': ''
            }
    
    def find_cover_file(self, video_file_path):
        """查找对应的封面文件"""
        try:
            base_path = os.path.splitext(video_file_path)[0]
            
            # 尝试不同的封面文件扩展名
            cover_extensions = ['_cover.jpg', '_cover.png', '.jpg', '.png']
            
            for ext in cover_extensions:
                cover_path = base_path + ext
                if os.path.exists(cover_path):
                    return cover_path
            
            # 在screenshots目录中查找
            screenshots_dir = os.path.join(os.path.dirname(video_file_path), 'screenshots')
            if os.path.exists(screenshots_dir):
                video_filename = os.path.basename(video_file_path)
                base_name = os.path.splitext(video_filename)[0]
                
                for ext in cover_extensions:
                    cover_path = os.path.join(screenshots_dir, base_name + ext)
                    if os.path.exists(cover_path):
                        return cover_path
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find cover file for {video_file_path}: {e}")
            return None
    
    def find_thumbnail_file(self, video_file_path):
        """查找对应的缩略图文件"""
        try:
            base_path = os.path.splitext(video_file_path)[0]
            
            # 尝试不同的缩略图文件扩展名
            thumbnail_extensions = ['_thumbnails.jpg', '_thumbnails.png', '_grid.jpg', '_grid.png']
            
            for ext in thumbnail_extensions:
                thumbnail_path = base_path + ext
                if os.path.exists(thumbnail_path):
                    return thumbnail_path
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find thumbnail file for {video_file_path}: {e}")
            return None
    
    def get_video_duration(self, video_file_path):
        """获取视频时长（需要ffprobe）"""
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', video_file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return self.format_duration(duration)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get video duration for {video_file_path}: {e}")
            return None
    
    def format_duration(self, seconds):
        """格式化时长"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except:
            return "00:00"
    
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
                
                # 检查实际录制状态
                recording_channels = []
                for channel in channels:
                    if self.check_recording_status(channel['channel_id']):
                        recording_channels.append(channel['channel_id'])
                
                return jsonify({
                    'status': 'running',
                    'total_channels': len(channels),
                    'live_channels': len(live_channels),
                    'recording_channels': len(recording_channels),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels')
        def get_channels():
            """获取频道列表"""
            try:
                channels = self.load_channel_list()
                # 为每个频道添加录制状态
                for channel in channels:
                    channel['is_recording'] = self.check_recording_status(channel['channel_id'])
                return jsonify(channels)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channels', methods=['POST'])
        def add_channel():
            """添加频道"""
            try:
                logger.info("Add channel request received")
                data = request.get_json()
                logger.info(f"Request data: {data}")
                channel_id = data.get('channel_id', '').strip()
                logger.info(f"Channel ID: '{channel_id}'")
                
                if not channel_id:
                    logger.warning("Empty channel ID provided")
                    return jsonify({'error': 'Channel ID is required'}), 400
                
                # 验证频道是否存在
                channel_info = self.get_channel_info(channel_id)
                logger.info(f"Channel info for {channel_id}: {channel_info}")
                logger.info(f"Channel name: '{channel_info.get('channelName')}'")
                logger.info(f"Channel name length: {len(channel_info.get('channelName', ''))}")
                
                if not channel_info.get('channelName'):
                    logger.warning(f"Channel validation failed for {channel_id}: no channelName")
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
                # 尝试多个可能的日志文件位置
                possible_log_files = [
                    os.path.join(os.path.dirname(__file__), 'logs', 'recorder.log'),
                    os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'recorder.log'),
                    os.path.join(os.getcwd(), 'logs', 'recorder.log'),
                    os.path.join(os.getcwd(), 'recorder.log')
                ]
                
                for log_file in possible_log_files:
                    if os.path.exists(log_file):
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            # 返回最后100行
                            return jsonify({'logs': lines[-100:]})
                
                # 如果没有找到日志文件，返回动态系统信息
                import datetime
                current_time = datetime.datetime.now()
                
                # 获取系统状态
                channels = self.load_channel_list()
                live_channels = [ch for ch in channels if ch['is_live']]
                recording_channels = []
                for channel in channels:
                    if self.check_recording_status(channel['channel_id']):
                        recording_channels.append(channel['channel_id'])
                
                # 获取录制历史统计
                config_path = os.path.join(os.getcwd(), 'src', 'config', 'config_local.json')
                recording_dir = 'download'
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            recording_dir = config.get('recording', {}).get('recording_save_root_dir', 'download')
                    except Exception as e:
                        pass
                
                recording_path = os.path.join(os.getcwd(), recording_dir)
                total_recordings = 0
                total_size_mb = 0
                
                if os.path.exists(recording_path):
                    for root, dirs, files in os.walk(recording_path):
                        for file in files:
                            if file.endswith(('.ts', '.mp4')):
                                total_recordings += 1
                                try:
                                    file_path = os.path.join(root, file)
                                    total_size_mb += os.path.getsize(file_path) / (1024 * 1024)
                                except:
                                    pass
                
                system_logs = [
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Web panel started",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: No log file found, using system logs",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Web panel is running on http://127.0.0.1:8080",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Socket.IO connection established",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Ready to receive commands",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: === Current Status ===",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Total channels: {len(channels)}",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Live channels: {len(live_channels)}",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Recording channels: {len(recording_channels)}",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Total recordings: {total_recordings}",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Total size: {total_size_mb:.2f} MB",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Recording directory: {recording_path}",
                    f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: Last update: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                ]
                
                # 添加频道详情
                if channels:
                    system_logs.append(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO System: === Channel Details ===")
                    for channel in channels:
                        status = "LIVE" if channel['is_live'] else "OFFLINE"
                        recording = "RECORDING" if self.check_recording_status(channel['channel_id']) else "IDLE"
                        system_logs.append(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} INFO Channel: {channel['channel_name']} - {status} - {recording}")
                
                return jsonify({'logs': system_logs})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording-history')
        def get_recording_history():
            """获取录制历史记录"""
            try:
                # 获取配置中的录制目录
                config_path = os.path.join(os.getcwd(), 'src', 'config', 'config_local.json')
                recording_dir = 'download'  # 默认目录
                
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            recording_dir = config.get('recording', {}).get('recording_save_root_dir', 'download')
                    except Exception as e:
                        logger.warning(f"Failed to read config for recording directory: {e}")
                
                recording_path = os.path.join(os.getcwd(), recording_dir)
                history = self.scan_recording_history(recording_path)
                
                return jsonify({
                    'success': True,
                    'recordings': history
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/channel-preview/<channel_id>')
        def preview_channel(channel_id):
            """预览频道信息"""
            try:
                channel_info = self.get_channel_info(channel_id)
                if channel_info:
                    return jsonify({
                        'success': True,
                        'channel': channel_info
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Channel not found'
                    }), 404
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
