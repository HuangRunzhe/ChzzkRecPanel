#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chzzk录制端主程序
从后端API获取频道列表，录制完成后POST记录到服务器
"""

import datetime
import json
import logging
import os
import re
import subprocess
import sys
import time
import threading
import shlex
import atexit
import requests
import zmq
import locale
import urllib3
import warnings
from typing import Dict, TypedDict, Union, List
from packaging import version

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# 导入本地模块
from api.chzzk import ChzzkAPI
from utils.telegram_notifier import TelegramNotifier
from utils.ffmpeg_converter import FFmpegConverter
from utils.chat_recorder import ChatRecorder
from utils.cookie_manager import CookieManager

STREAMLINK_MIN_VERSION = "6.7.4"

# 设置locale
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    pass

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fmt = logging.Formatter("{asctime} {levelname} {name} {message}", style="{")
stream_hdlr = logging.StreamHandler()
stream_hdlr.setFormatter(fmt)
logger.addHandler(hdlr=stream_hdlr)

def escape_filename(s: str) -> str:
    """移除文件名中的特殊字符"""
    return re.sub(r"[/\\?%*:|\"<>.\n{}]", "", s)

def truncate_long_name(s: str) -> str:
    """截断过长的名称"""
    return (s[:75] + '..') if len(s) > 77 else s

def check_streamlink() -> bool:
    """检查streamlink是否安装且版本符合要求"""
    try:
        ret = subprocess.check_output(["streamlink", "--version"], universal_newlines=True)
        re_ver = re.search(r"streamlink (\d+)\.(\d+)\.(\d+)", ret, flags=re.IGNORECASE)

        if not re_ver:
            raise FileNotFoundError

        s_ver = version.parse('.'.join(re_ver.groups()))
        logger.info(f"Streamlink version: {s_ver}")
        return s_ver >= version.parse(STREAMLINK_MIN_VERSION)
    except FileNotFoundError:
        logger.error("Streamlink not found. Install streamlink first then launch again.")
        sys.exit(1)

class RecorderProcess(TypedDict):
    recorder: Union[None, subprocess.Popen]
    path: Union[None, str]
    time: Union[None, datetime.datetime]
    record_id: Union[None, int]  # 录制记录ID

class MultiChzzkRecorder:
    def __init__(self, config_path: str = "config_local.json") -> None:
        logger.info("Initializing Multi Chzzk Recorder...")

        if not check_streamlink():
            logger.error("Streamlink version check failed")
            sys.exit(1)

        # 加载配置
        self.config = self.load_config(config_path)
        
        # 初始化 Cookie 管理器
        self.cookie_manager = CookieManager(config_path)
        
        # 初始化组件
        self.chzzk_api = ChzzkAPI(
            nid_aut=self.config['recording']['nid_aut'],
            nid_ses=self.config['recording']['nid_ses']
        )
        
        # 设置为本地模式
        self.api_available = False
        self.api_client = None
        
        # 初始化通知器
        try:
            self.telegram_notifier = TelegramNotifier(
                bot_token=self.config['notifications']['telegram_bot_token'],
                chat_id=self.config['notifications']['telegram_chat_id']
            )
        except Exception as e:
            logger.warning(f"Telegram通知器初始化失败: {e}")
            self.telegram_notifier = None
        self.ffmpeg_converter = FFmpegConverter(self.config['processing'])
        
        # 录制状态
        self.recorder_processes: Dict[str, RecorderProcess] = {}
        self.record_dict: Dict[str, Dict] = {}
        self.chat_recorders: Dict[str, ChatRecorder] = {}  # 弹幕录制器
        
        # ZMQ通信
        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind(f"tcp://*:{self.config['system']['zmq_port']}")
        
        # 注册退出处理
        atexit.register(self.cleanup)
        
        logger.info("Multi Chzzk Recorder initialized successfully")

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        # 如果路径是相对路径，则相对于项目根目录
        if not os.path.isabs(config_path):
            # 获取项目根目录（recorder目录）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, config_path)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def get_monitored_channels(self) -> List[Dict]:
        """获取监控频道列表 - 从本地文件读取"""
        try:
            channels = self.load_channels_from_file()
            if channels:
                logger.info(f"Loaded {len(channels)} channels from local file")
                return channels
        except Exception as e:
            logger.error(f"Failed to load channels from file: {e}")
        
        logger.warning("No channels available from local file")
        return []
    
    def load_channels_from_file(self) -> List[Dict]:
        """从本地record_list.txt文件加载频道列表"""
        try:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            record_list_path = os.path.join(project_root, 'src', 'config', 'record_list.txt')
            if not os.path.exists(record_list_path):
                logger.warning("record_list.txt not found, using empty channel list")
                return []
            
            channels = []
            with open(record_list_path, 'r', encoding='utf-8') as f:
                for line in f:
                    channel_id = line.strip()
                    if channel_id:
                        channels.append({
                            'channel_id': channel_id,
                            'channel_name': f"Channel_{channel_id[:8]}",
                            'channel_image': ''
                        })
            
            return channels
        except Exception as e:
            logger.error(f"Failed to load channels from file: {e}")
            return []

    def check_channel_status(self, channel_id: str) -> Dict:
        """检查频道状态"""
        try:
            # 使用check_live方法获取直播状态
            is_live, stream_data = self.chzzk_api.check_live(channel_id)
            if is_live is None:
                logger.warning(f"Failed to check live status for {channel_id}")
                return {'isLive': False, 'liveTitle': '', 'viewerCount': 0}
            
            if is_live and stream_data:
                return {
                    'isLive': True,
                    'liveTitle': stream_data.get('liveTitle', ''),
                    'viewerCount': stream_data.get('concurrentUserCount', 0),
                    'channelName': stream_data.get('channelName', ''),
                    'channelImageUrl': stream_data.get('channelImageUrl', ''),
                    'liveImageUrl': stream_data.get('liveImageUrl', ''),
                    'openDate': stream_data.get('openDate', '')
                }
            else:
                return {'isLive': False, 'liveTitle': '', 'viewerCount': 0}
        except Exception as e:
            logger.error(f"Failed to check channel status for {channel_id}: {e}")
            return {'isLive': False, 'liveTitle': '', 'viewerCount': 0}

    def get_recording_quality(self, user_id: int = None) -> str:
        """根据订阅状态获取录制质量"""
        try:
            if not user_id or not self.api_available or not self.api_client:
                # 默认返回配置的质量
                return self.config['recording']['quality']
            
            # 从API获取用户订阅状态
            response = self.api_client.get_recording_quality(user_id)
            if response and 'quality' in response:
                return response['quality']
            else:
                return self.config['recording']['quality']
                
        except Exception as e:
            logger.warning(f"Failed to get recording quality for user {user_id}: {e}")
            return self.config['recording']['quality']

    def start_recording(self, channel_id: str, channel_data: Dict, user_id: int = None) -> bool:
        """开始录制"""
        try:
            # 检查频道状态
            status = self.check_channel_status(channel_id)
            if not status['isLive']:
                return False
            
            # 根据订阅状态确定录制质量
            recording_quality = self.get_recording_quality(user_id)
            logger.info(f"Using recording quality: {recording_quality} for channel {channel_id}")
            
            # 创建录制记录
            record_id = None
            if self.api_available and self.api_client:
                try:
                    # 确保stream_title不为空
                    stream_title = status.get('liveTitle', '')
                    if not stream_title:
                        stream_title = f"Live Stream - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    
                    # 优先使用API返回的频道信息，如果没有则使用默认值
                    channel_name = status.get('channelName', '') or channel_data.get('channel_name', f'Channel_{channel_id[:8]}')
                    channel_image = status.get('channelImageUrl', '') or channel_data.get('channel_image', '')
                    
                    record_id = self.api_client.create_recording(
                        channel_id=channel_id,
                        channel_name=channel_name,
                        stream_title=stream_title,
                        channel_image=channel_image,
                        quality=recording_quality,
                        user_id=user_id
                    )
                    if record_id:
                        logger.info(f"Created recording record via API: {record_id}")
                except Exception as e:
                    logger.warning(f"Failed to create recording record via API: {e}")
                    record_id = None
            
            # API不可用或失败时，使用本地记录ID
            if not record_id:
                record_id = f"local_{int(time.time())}_{channel_id[:8]}"
                logger.info(f"Using local record ID: {record_id}")
            
            # 准备录制路径
            now = datetime.datetime.now()
            stream_started = now.strftime(self.config['recording']['time_format'])
            escaped_title = escape_filename(status['liveTitle'])
            username = channel_data.get('channel_name', status.get('channelName', 'Unknown'))
            
            filename = self.config['recording']['file_name_format'].format(
                username=username,
                stream_started=stream_started,
                escaped_title=escaped_title
            )
            
            rec_file_path = os.path.join(
                self.config['recording']['recording_save_root_dir'],
                username,
                filename
            )
            
            # 创建目录
            os.makedirs(os.path.dirname(rec_file_path), exist_ok=True)
            
            # 构建streamlink命令
            stream_url = f"https://chzzk.naver.com/live/{channel_id}"
            command = [
                "streamlink",
                stream_url,
                recording_quality,  # 使用动态质量
                "-o", rec_file_path,
                "--retry-streams", "5",
                "--retry-max", "10"
            ]
            
            # 开始录制
            logger.info(f"Starting recording: {username} - {status['liveTitle']}")
            logger.info(f"Command: {' '.join(command)}")
            
            recorder = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8'
            )
            
            # 保存录制信息
            self.recorder_processes[channel_id] = {
                'recorder': recorder,
                'path': rec_file_path,
                'time': now,
                'record_id': record_id
            }
            
            self.record_dict[channel_id] = {
                'channelName': username,
                'channelImageUrl': channel_data.get('channel_image', ''),
                'liveTitle': status['liveTitle'],
                'viewerCount': status['viewerCount']
            }
            
            # 启动弹幕录制（如果启用）
            if self.config['recording'].get('record_chat', False):
                try:
                    chat_output_dir = os.path.join(
                        self.config['recording']['recording_save_root_dir'],
                        username
                    )
                    chat_recorder = ChatRecorder(channel_id, chat_output_dir)
                    if chat_recorder.start():
                        self.chat_recorders[channel_id] = chat_recorder
                        logger.info(f"Chat recording started for channel {channel_id}")
                    else:
                        logger.warning(f"Failed to start chat recording for channel {channel_id}")
                except Exception as e:
                    logger.warning(f"Error starting chat recording: {e}")
            
            # 发送通知
            self.send_recording_start_notification(channel_id, status)
            
            # 启动延迟封面截取任务
            self.start_delayed_cover_capture(channel_id, rec_file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording for {channel_id}: {e}")
            return False

    def start_delayed_cover_capture(self, channel_id: str, recording_file_path: str):
        """启动延迟封面截取任务"""
        def delayed_capture():
            try:
                # 等待15秒让录制稳定
                logger.info(f"Waiting 15 seconds before capturing cover for {channel_id}...")
                time.sleep(15)
                
                # 检查录制是否还在进行
                if channel_id in self.recorder_processes:
                    logger.info(f"Starting cover capture for {channel_id}")
                    cover_path = self.capture_cover_from_recording(channel_id, recording_file_path)
                    
                    if cover_path:
                        logger.info(f"Cover captured successfully: {cover_path}")
                        # 可以在这里更新数据库中的封面路径
                        try:
                            if channel_id in self.recorder_processes:
                                record_id = self.recorder_processes[channel_id]['record_id']
                                # 这里可以调用API更新封面路径
                                logger.info(f"Cover ready for record ID: {record_id}")
                        except Exception as e:
                            logger.warning(f"Failed to update cover path in database: {e}")
                    else:
                        logger.warning(f"Failed to capture cover for {channel_id}")
                else:
                    logger.info(f"Recording stopped for {channel_id}, skipping cover capture")
                    
            except Exception as e:
                logger.error(f"Error in delayed cover capture for {channel_id}: {e}")
        
        # 在后台线程中执行延迟封面截取
        cover_thread = threading.Thread(target=delayed_capture, daemon=True)
        cover_thread.start()
        logger.info(f"Delayed cover capture task started for {channel_id}")

    def stop_recording(self, channel_id: str) -> bool:
        """停止录制"""
        try:
            if channel_id not in self.recorder_processes:
                return False
            
            process_info = self.recorder_processes[channel_id]
            recorder = process_info['recorder']
            record_id = process_info['record_id']
            file_path = process_info['path']
            
            if recorder and recorder.poll() is None:
                # 终止录制进程
                recorder.terminate()
                try:
                    recorder.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    recorder.kill()
                    recorder.wait()
            
            # 检查文件是否存在并获取大小
            file_size = 0
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            
            # 尝试更新录制记录（API可用时）
            try:
                success = self.api_client.end_recording(
                    record_id=record_id,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    status='completed'
                )
                
                if success:
                    logger.info(f"Recording completed and synced to API for {channel_id}")
                else:
                    logger.warning(f"Failed to sync recording to API for {channel_id}")
            except Exception as e:
                logger.warning(f"Failed to sync recording to API: {e}")
                logger.info(f"Recording completed locally for {channel_id}")
            
            # 停止弹幕录制
            if channel_id in self.chat_recorders:
                try:
                    chat_recorder = self.chat_recorders[channel_id]
                    chat_file_path = chat_recorder.get_chat_file_path()
                    if chat_recorder.stop():
                        logger.info(f"Chat recording stopped for channel {channel_id}")
                        if chat_file_path:
                            logger.info(f"Chat file saved: {chat_file_path}")
                    else:
                        logger.warning(f"Failed to stop chat recording for channel {channel_id}")
                    del self.chat_recorders[channel_id]
                except Exception as e:
                    logger.warning(f"Error stopping chat recording: {e}")
            
            # 发送通知
            self.send_recording_end_notification(channel_id, file_path, file_size)
            
            # 异步处理文件转换
            if self.config['processing']['auto_convert_to_mp4']:
                threading.Thread(
                    target=self.process_recording_file,
                    args=(channel_id, file_path, record_id),
                    daemon=True
                ).start()
            
            # 清理进程信息
            del self.recorder_processes[channel_id]
            if channel_id in self.record_dict:
                del self.record_dict[channel_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording for {channel_id}: {e}")
            return False

    def process_recording_file(self, channel_id: str, file_path: str, record_id: int):
        """处理录制文件（转换、生成缩略图等）"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Recording file not found: {file_path}")
                return
            
            # 转换为MP4
            if self.config['processing']['auto_convert_to_mp4']:
                mp4_path = file_path.replace('.ts', '.mp4')
                success = self.ffmpeg_converter.convert_ts_to_mp4(
                    ts_file_path=file_path,
                    mp4_file_path=mp4_path
                )
                
                if success and os.path.exists(mp4_path):
                    # 尝试更新文件路径（API可用时）
                    try:
                        self.api_client.update_recording_status(
                            record_id, 'completed', mp4_path
                        )
                        logger.info(f"File conversion synced to API: {mp4_path}")
                    except Exception as e:
                        logger.warning(f"Failed to sync file conversion to API: {e}")
                        logger.info(f"File converted locally: {mp4_path}")
                    
                    # 删除原始TS文件
                    if self.config['processing']['delete_ts_after_conversion']:
                        os.remove(file_path)
                        file_path = mp4_path
                    
                    logger.info(f"File converted successfully: {mp4_path}")
                else:
                    logger.error(f"File conversion failed: {file_path}")
            
            # 生成缩略图
            if self.config['processing']['generate_thumbnails']:
                self.generate_thumbnails(file_path, record_id)
                
        except Exception as e:
            logger.error(f"Failed to process recording file: {e}")

    def generate_thumbnails(self, file_path: str, record_id: int):
        """生成缩略图"""
        try:
            # 生成多个缩略图
            thumbnails = self.ffmpeg_converter.generate_thumbnails(
                video_path=file_path,
                count=self.config['processing']['thumbnail_count'],
                width=self.config['processing']['thumbnail_width'],
                height=self.config['processing']['thumbnail_height']
            )
            
            if thumbnails:
                # 创建缩略图网格
                grid_path = self.ffmpeg_converter.create_thumbnail_grid(
                    thumbnail_paths=thumbnails,
                    output_path=file_path.replace('.mp4', '_thumbnails.jpg')
                )
                
                if grid_path:
                    # 尝试更新录制记录（API可用时）
                    try:
                        self.api_client.update_recording_status(
                            record_id, 'completed', file_path, grid_path
                        )
                        logger.info(f"Thumbnails generated and synced to API: {grid_path}")
                    except Exception as e:
                        logger.warning(f"Failed to sync thumbnails to API: {e}")
                        logger.info(f"Thumbnails generated locally: {grid_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnails: {e}")

    def capture_cover_from_recording(self, channel_id: str, recording_file_path: str) -> str:
        """从正在录制的视频中截取封面"""
        try:
            # 等待录制文件有一定大小（至少几MB）
            max_wait_time = 30  # 最多等待30秒
            wait_interval = 2   # 每2秒检查一次
            waited = 0
            
            while waited < max_wait_time:
                if os.path.exists(recording_file_path):
                    file_size = os.path.getsize(recording_file_path)
                    if file_size > 1024 * 1024:  # 至少1MB
                        logger.info(f"Recording file ready for cover capture: {file_size} bytes")
                        break
                time.sleep(wait_interval)
                waited += wait_interval
                logger.info(f"Waiting for recording file to be ready... ({waited}s)")
            
            if not os.path.exists(recording_file_path):
                logger.error(f"Recording file not found: {recording_file_path}")
                return None
            
            # 创建截图保存目录
            screenshot_dir = os.path.join(self.config['recording']['recording_save_root_dir'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # 生成封面文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{channel_id}_{timestamp}_cover.jpg"
            cover_path = os.path.join(screenshot_dir, filename)
            
            # 使用ffmpeg从录制视频中截取封面（取视频中间位置的一帧）
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', recording_file_path,
                '-ss', '5',  # 跳过前5秒
                '-vframes', '1',  # 只截取一帧
                '-vf', f'scale={self.config["processing"]["cover_image_width"]}:{self.config["processing"]["cover_image_height"]}',
                '-q:v', '2',  # 高质量
                '-y',  # 覆盖输出文件
                cover_path
            ]
            
            logger.info(f"Capturing cover from recording: {recording_file_path}")
            logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(cover_path):
                file_size = os.path.getsize(cover_path)
                if file_size > 0:
                    logger.info(f"Cover captured successfully: {cover_path} ({file_size} bytes)")
                    return cover_path
                else:
                    logger.error("Captured cover file is empty")
                    return None
            else:
                logger.error(f"Failed to capture cover: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to capture cover from recording: {e}")
            return None

    def download_and_save_screenshot(self, channel_id: str, status: Dict) -> str:
        """下载并保存直播截图（备用方法）"""
        try:
            # 尝试从状态中获取直播图片URL
            live_image_url = status.get('liveImageUrl', '')
            logger.info(f"Live image URL from status: {live_image_url}")
            
            if not live_image_url:
                # 如果没有直播图片URL，尝试从频道信息获取
                logger.info("No live image URL in status, trying channel info...")
                channel_info = self.chzzk_api.get_channel_info(channel_id)
                if channel_info:
                    live_image_url = channel_info.get('liveImageUrl', '')
                    logger.info(f"Live image URL from channel info: {live_image_url}")
                    
                    if not live_image_url:
                        live_image_url = channel_info.get('channelImageUrl', '')
                        logger.info(f"Using channel image URL as fallback: {live_image_url}")
                else:
                    logger.warning("Failed to get channel info")
            
            # 如果API没有提供图片URL，尝试从直播流截取
            if not live_image_url:
                logger.info("No image URL from API, trying to capture from live stream...")
                return self.capture_screenshot_from_stream(channel_id)
            
            # 创建截图保存目录
            screenshot_dir = os.path.join(self.config['recording']['recording_save_root_dir'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{channel_id}_{timestamp}.jpg"
            file_path = os.path.join(screenshot_dir, filename)
            
            # 处理URL中的占位符
            if '{type}' in live_image_url:
                # 尝试不同的图片类型
                image_types = ['thumbnail', 'cover', 'preview']
                for image_type in image_types:
                    processed_url = live_image_url.replace('{type}', image_type)
                    logger.info(f"Trying image type '{image_type}': {processed_url}")
                    
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        
                        response = requests.get(processed_url, headers=headers, timeout=10)
                        if response.status_code == 200 and len(response.content) > 0:
                            logger.info(f"Successfully downloaded image with type '{image_type}'")
                            break
                        else:
                            logger.warning(f"Failed to download image with type '{image_type}': {response.status_code}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error downloading image with type '{image_type}': {e}")
                        continue
                else:
                    logger.error("All image types failed to download")
                    return None
            else:
                # 没有占位符，直接下载
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                logger.info(f"Downloading screenshot from: {live_image_url}")
                response = requests.get(live_image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 检查响应内容
            if len(response.content) == 0:
                logger.warning("Downloaded image is empty")
                return None
            
            # 保存图片
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # 验证文件是否保存成功
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"Screenshot saved successfully: {file_path} ({os.path.getsize(file_path)} bytes)")
                return file_path
            else:
                logger.error("Failed to save screenshot file")
                return None
            
        except Exception as e:
            logger.error(f"Failed to download screenshot for {channel_id}: {e}")
            return None
    
    def capture_screenshot_from_stream(self, channel_id: str) -> str:
        """从直播流截取截图"""
        try:
            # 创建截图保存目录
            screenshot_dir = os.path.join(self.config['recording']['recording_save_root_dir'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_video = os.path.join(screenshot_dir, f"temp_{channel_id}_{timestamp}.ts")
            screenshot_file = os.path.join(screenshot_dir, f"{channel_id}_{timestamp}.jpg")
            
            # 使用streamlink录制几秒钟的视频
            stream_url = f"https://chzzk.naver.com/live/{channel_id}"
            
            # 构建streamlink命令录制短视频
            streamlink_cmd = [
                'streamlink',
                stream_url,
                self.config['recording']['quality'],
                '-o', temp_video,
                '--retry-streams', '3',
                '--retry-max', '5',
                '--stream-timeout', '10'  # 流超时
            ]
            
            logger.info(f"Recording short video for screenshot: {stream_url}")
            logger.info(f"Streamlink command: {' '.join(streamlink_cmd)}")
            
            # 启动streamlink录制进程
            process = subprocess.Popen(
                streamlink_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待更长时间让视频开始录制
            time.sleep(8)
            
            # 终止录制进程
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # 检查进程输出
            stdout, stderr = process.communicate()
            if stderr:
                logger.warning(f"Streamlink stderr: {stderr}")
            
            # 检查临时视频文件是否存在
            if not os.path.exists(temp_video):
                logger.error(f"Temporary video file not created: {temp_video}")
                return None
            
            file_size = os.path.getsize(temp_video)
            if file_size == 0:
                logger.error(f"Temporary video file is empty: {temp_video}")
                return None
            
            logger.info(f"Temporary video recorded: {temp_video} ({file_size} bytes)")
            
            # 使用ffmpeg从视频中提取一帧
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', temp_video,
                '-vframes', '1',  # 只截取一帧
                '-q:v', '2',      # 高质量
                '-y',             # 覆盖输出文件
                screenshot_file
            ]
            
            logger.info(f"Extracting screenshot from video")
            logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # 执行ffmpeg命令
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=15  # 15秒超时
            )
            
            # 清理临时视频文件
            try:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
                    logger.info(f"Cleaned up temporary video: {temp_video}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary video: {e}")
            
            if result.returncode == 0:
                # 检查截图文件是否生成成功
                if os.path.exists(screenshot_file) and os.path.getsize(screenshot_file) > 0:
                    screenshot_size = os.path.getsize(screenshot_file)
                    logger.info(f"Screenshot captured successfully: {screenshot_file} ({screenshot_size} bytes)")
                    return screenshot_file
                else:
                    logger.error("Screenshot file was not created or is empty")
                    return None
            else:
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr}")
                logger.error(f"FFmpeg stdout: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout while capturing screenshot")
            return None
        except Exception as e:
            logger.error(f"Failed to capture screenshot from stream: {e}")
            return None

    def send_discord_notification(self, title: str, description: str, color: int = 0x00FF00, image_path: str = None):
        """发送Discord通知"""
        try:
            if not self.config['notifications']['use_discord_bot']:
                logger.info("Discord通知已禁用")
                return
            
            token = self.config['notifications']['discord_bot_token']
            channel_id = self.config['notifications']['discord_channel_id']
            
            if not token or not channel_id:
                logger.warning("Discord配置无效")
                return
            
            # 创建embed消息
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.datetime.now().isoformat(),
                "author": {
                    "name": "Chzzk Recorder",
                    "icon_url": "https://ssl.pstatic.net/static/nng/glive/icon/favicon.png"
                }
            }
            
            # 如果有图片，上传到Discord
            if image_path and os.path.exists(image_path):
                try:
                    # 使用multipart/form-data上传文件
                    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
                    headers = {
                        "Authorization": f"Bot {token}"
                    }
                    
                    # 准备文件上传
                    with open(image_path, 'rb') as f:
                        files = {
                            'file': (os.path.basename(image_path), f, 'image/jpeg')
                        }
                        
                        # 准备payload
                        payload = {
                            'payload_json': json.dumps({
                                "embeds": [embed]
                            })
                        }
                        
                        response = requests.post(url, headers=headers, files=files, data=payload, timeout=30)
                        
                        if response.status_code == 200:
                            logger.info("Discord通知发送成功（带图片）")
                        else:
                            logger.error(f"Discord通知发送失败: {response.status_code} - {response.text}")
                            
                except Exception as e:
                    logger.error(f"Failed to upload image to Discord: {e}")
                    # 如果图片上传失败，发送纯文本消息
                    self.send_discord_text_notification(title, description, color)
            else:
                # 发送纯文本消息
                self.send_discord_text_notification(title, description, color)
                
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def send_discord_text_notification(self, title: str, description: str, color: int = 0x00FF00):
        """发送Discord纯文本通知"""
        try:
            token = self.config['notifications']['discord_bot_token']
            channel_id = self.config['notifications']['discord_channel_id']
            
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.datetime.now().isoformat(),
                "author": {
                    "name": "Chzzk Recorder",
                    "icon_url": "https://ssl.pstatic.net/static/nng/glive/icon/favicon.png"
                }
            }
            
            message_data = {
                "embeds": [embed]
            }
            
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=message_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("Discord通知发送成功（纯文本）")
            else:
                logger.error(f"Discord通知发送失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to send Discord text notification: {e}")

    def send_recording_start_notification(self, channel_id: str, status: Dict):
        """发送录制开始通知"""
        try:
            # 生成直播链接
            live_url = f"https://chzzk.naver.com/live/{channel_id}"
            
            message = f"""🎥 Recording Started

Channel: {status.get('channelName', 'Unknown')}
Title: {status.get('liveTitle', 'No title')}
Viewers: {status.get('viewerCount', 0):,}

🔗 Watch Live: {live_url}

---
📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # 下载并保存直播截图
            screenshot_path = self.download_and_save_screenshot(channel_id, status)
            
            # 发送Telegram通知
            if self.config['notifications']['use_telegram_bot'] and self.telegram_notifier:
                if screenshot_path and os.path.exists(screenshot_path):
                    self.telegram_notifier.send_photo(screenshot_path, message)
                    logger.info(f"Sent Telegram notification with screenshot: {screenshot_path}")
                else:
                    self.telegram_notifier.send_message(message)
                    logger.info("Sent Telegram notification without screenshot")
            
            # 发送Discord通知
            if self.config['notifications']['use_discord_bot']:
                # 为Discord创建更详细的消息
                discord_message = f"""**Channel:** {status.get('channelName', 'Unknown')}
**Title:** {status.get('liveTitle', 'No title')}
**Viewers:** {status.get('viewerCount', 0):,}

🔗 **[Watch Live Stream]({live_url})**

---
📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
                self.send_discord_notification(
                    "🎥 Recording Started", 
                    discord_message, 
                    0x00FF00, 
                    screenshot_path
                )
                logger.info("Sent Discord notification")
            
        except Exception as e:
            logger.error(f"Failed to send recording start notification: {e}")

    def send_recording_end_notification(self, channel_id: str, file_path: str, file_size: int):
        """发送录制结束通知"""
        try:
            # 转换为GB单位
            file_size_gb = round(file_size / (1024 * 1024 * 1024), 2)
            duration = "Unknown"
            
            # 尝试获取录制时长
            if channel_id in self.recorder_processes:
                start_time = self.recorder_processes[channel_id]['time']
                duration_seconds = int((datetime.datetime.now() - start_time).total_seconds())
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # 生成直播链接
            live_url = f"https://chzzk.naver.com/live/{channel_id}"
            
            message = f"""✅ Recording Completed

File: {os.path.basename(file_path)}
Size: {file_size_gb} GB
Duration: {duration}

🔗 Channel: {live_url}

---
📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # 发送Telegram通知
            if self.config['notifications']['use_telegram_bot'] and self.telegram_notifier:
                self.telegram_notifier.send_message(message)
                logger.info("Sent Telegram recording end notification")
            
            # 发送Discord通知
            if self.config['notifications']['use_discord_bot']:
                # 为Discord创建更详细的消息
                discord_message = f"""**File:** {os.path.basename(file_path)}
**Size:** {file_size_gb} GB
**Duration:** {duration}

🔗 **[Visit Channel]({live_url})**

---
📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
                self.send_discord_notification(
                    "✅ Recording Completed", 
                    discord_message, 
                    0x00FF00
                )
                logger.info("Sent Discord recording end notification")
            
        except Exception as e:
            logger.error(f"Failed to send recording end notification: {e}")

    def run(self):
        """主运行循环"""
        logger.info("Starting Multi Chzzk Recorder...")
        
        while True:
            try:
                # 检查 Cookie 有效性
                if not self.cookie_manager.check_and_update_cookies():
                    logger.error("Cookie 已失效，跳过本次检查")
                    time.sleep(self.config['recording']['interval'])
                    continue
                
                # 获取监控频道列表
                channels = self.get_monitored_channels()
                if not channels:
                    logger.warning("No monitored channels found")
                    time.sleep(self.config['recording']['interval'])
                    continue
                
                # 检查每个频道
                for channel in channels:
                    channel_id = channel['channel_id']
                    
                    try:
                        # 检查频道状态
                        status = self.check_channel_status(channel_id)
                        
                        if status['isLive']:
                            # 如果正在直播且未录制，开始录制
                            if channel_id not in self.recorder_processes:
                                logger.info(f"Channel {channel_id} is live, starting recording...")
                                self.start_recording(channel_id, channel)
                        else:
                            # 如果不在直播但正在录制，停止录制
                            if channel_id in self.recorder_processes:
                                logger.info(f"Channel {channel_id} is offline, stopping recording...")
                                self.stop_recording(channel_id)
                    
                    except Exception as e:
                        logger.error(f"Error processing channel {channel_id}: {e}")
                
                # 等待下次检查
                time.sleep(self.config['recording']['interval'])
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(10)

    def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up resources...")
        
        # 停止所有录制
        for channel_id in list(self.recorder_processes.keys()):
            self.stop_recording(channel_id)
        
        # 停止所有弹幕录制
        for channel_id in list(self.chat_recorders.keys()):
            try:
                self.chat_recorders[channel_id].stop()
                logger.info(f"Chat recording stopped for channel {channel_id}")
            except Exception as e:
                logger.warning(f"Error stopping chat recording for {channel_id}: {e}")
        self.chat_recorders.clear()
        
        # 关闭ZMQ
        if hasattr(self, 'zmq_socket'):
            self.zmq_socket.close()
        if hasattr(self, 'zmq_context'):
            self.zmq_context.term()
        
        logger.info("Cleanup completed")

def main():
    """主函数"""
    try:
        # 从环境变量获取配置文件路径
        config_path = os.environ.get('CONFIG_PATH', 'src/config/config_local.json')
        recorder = MultiChzzkRecorder(config_path)
        recorder.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
