#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class FFmpegConverter:
    """FFmpeg视频转码器"""
    
    def __init__(self, config):
        self.config = config
        self.auto_convert = config.get('auto_convert_to_mp4', True)
        self.delete_ts = config.get('delete_ts_after_conversion', True)
        self.preset = config.get('ffmpeg_preset', 'medium')
        self.crf = config.get('ffmpeg_crf', 23)
        
        # 缩略图配置
        self.generate_thumbnails = config.get('generate_thumbnails', True)
        self.thumbnail_count = config.get('thumbnail_count', 3)
        self.thumbnail_width = config.get('thumbnail_width', 320)
        self.thumbnail_height = config.get('thumbnail_height', 180)
        self.cover_width = config.get('cover_image_width', 1280)
        self.cover_height = config.get('cover_image_height', 720)
        
    def check_ffmpeg(self):
        """检查FFmpeg是否安装"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("FFmpeg已安装")
                return True
            else:
                logger.error("FFmpeg未正确安装")
                return False
        except FileNotFoundError:
            logger.error("FFmpeg未找到，请先安装FFmpeg")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg检查超时")
            return False
        except Exception as e:
            logger.error(f"检查FFmpeg时出错: {e}")
            return False
    
    def convert_ts_to_mp4(self, ts_file_path, mp4_file_path=None):
        """将TS文件转换为MP4"""
        if not self.auto_convert:
            logger.info("自动转码已禁用")
            return False
            
        if not self.check_ffmpeg():
            logger.error("FFmpeg不可用，跳过转码")
            return False
            
        if not os.path.exists(ts_file_path):
            logger.error(f"TS文件不存在: {ts_file_path}")
            return False
        
        # 生成MP4文件路径
        if mp4_file_path is None:
            mp4_file_path = ts_file_path.replace('.ts', '.mp4')
        
        logger.info(f"开始转码: {ts_file_path} -> {mp4_file_path}")
        
        try:
            # 构建FFmpeg命令 - 使用快速转换模式
            cmd = [
                'ffmpeg',
                '-i', ts_file_path,
                '-c', 'copy',  # 直接复制流，不重新编码
                '-movflags', '+faststart',
                '-y',  # 覆盖输出文件
                mp4_file_path
            ]
            
            # 执行转码
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1小时超时
            
            if result.returncode == 0:
                end_time = time.time()
                duration = end_time - start_time
                
                # 获取文件大小
                ts_size = os.path.getsize(ts_file_path)
                mp4_size = os.path.getsize(mp4_file_path)
                
                logger.info(f"转码完成! 耗时: {duration:.2f}秒")
                logger.info(f"TS文件大小: {self.format_file_size(ts_size)}")
                logger.info(f"MP4文件大小: {self.format_file_size(mp4_size)}")
                logger.info(f"压缩率: {(1 - mp4_size/ts_size)*100:.1f}%")
                
                # 生成缩略图
                if self.generate_thumbnails:
                    self.generate_video_thumbnails(mp4_file_path)
                
                # 删除TS文件
                if self.delete_ts:
                    try:
                        os.remove(ts_file_path)
                        logger.info(f"已删除TS文件: {ts_file_path}")
                    except Exception as e:
                        logger.error(f"删除TS文件失败: {e}")
                
                return True
            else:
                logger.error(f"转码失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("转码超时（1小时）")
            return False
        except Exception as e:
            logger.error(f"转码过程中出错: {e}")
            return False
    
    def convert_async(self, ts_file_path, mp4_file_path=None, callback=None):
        """异步转码"""
        def convert_thread():
            try:
                success = self.convert_ts_to_mp4(ts_file_path, mp4_file_path)
                if callback:
                    callback(success, ts_file_path, mp4_file_path or ts_file_path.replace('.ts', '.mp4'))
            except Exception as e:
                logger.error(f"异步转码出错: {e}")
                if callback:
                    callback(False, ts_file_path, mp4_file_path or ts_file_path.replace('.ts', '.mp4'))
        
        thread = threading.Thread(target=convert_thread)
        thread.daemon = True
        thread.start()
        return thread
    
    def generate_video_thumbnails(self, video_path):
        """生成视频缩略图"""
        if not self.generate_thumbnails:
            return []
        
        try:
            # 获取视频时长
            duration = self.get_video_duration(video_path)
            if duration is None:
                logger.error("无法获取视频时长，跳过缩略图生成")
                return []
            
            # 生成缩略图目录
            thumbnail_dir = os.path.join(os.path.dirname(video_path), "thumbnails")
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            generated_files = []
            
            # 1. 生成多张小图（用于拼接）
            temp_images = []
            for i in range(self.thumbnail_count):
                # 计算时间点（均匀分布）
                time_point = (duration / (self.thumbnail_count + 1)) * (i + 1)
                
                # 生成临时图片文件名
                temp_path = os.path.join(thumbnail_dir, f"{base_name}_temp_{i+1}.jpg")
                
                # 构建FFmpeg命令 - 将-ss放在-i之前以快速跳转
                cmd = [
                    'ffmpeg',
                    '-ss', str(time_point),  # 先跳转到指定时间
                    '-i', video_path,
                    '-vframes', '1',
                    '-vf', f'scale={self.thumbnail_width}:{self.thumbnail_height}',
                    '-q:v', '2',  # 高质量
                    '-y',
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    temp_images.append(temp_path)
                    logger.info(f"生成临时图片: {temp_path}")
                else:
                    logger.error(f"生成临时图片失败: {result.stderr}")
            
            # 2. 拼接成一张缩略图
            if temp_images:
                thumbnail_path = os.path.join(thumbnail_dir, f"{base_name}_thumbnail.jpg")
                if self.create_thumbnail_grid(temp_images, thumbnail_path):
                    generated_files.append(thumbnail_path)
                    logger.info(f"生成拼接缩略图: {thumbnail_path}")
            
            # 3. 生成封面图（单张大图）
            cover_path = os.path.join(thumbnail_dir, f"{base_name}_cover.jpg")
            if self.generate_cover_image(video_path, cover_path):
                generated_files.append(cover_path)
                logger.info(f"生成封面图: {cover_path}")
            
            # 4. 清理临时文件
            for temp_img in temp_images:
                try:
                    os.remove(temp_img)
                except:
                    pass
            
            logger.info(f"缩略图生成完成，共生成 {len(generated_files)} 张图片")
            return generated_files
            
        except Exception as e:
            logger.error(f"生成缩略图时出错: {e}")
            return []
    
    def create_thumbnail_grid(self, image_paths, output_path):
        """将多张图片拼接成一张缩略图"""
        try:
            if not image_paths:
                return False
            
            # 计算网格布局（优化6张图片的布局）
            count = len(image_paths)
            if count == 6:
                # 6张图片使用3x2布局
                cols, rows = 3, 2
            elif count == 4:
                # 4张图片使用2x2布局
                cols, rows = 2, 2
            elif count == 9:
                # 9张图片使用3x3布局
                cols, rows = 3, 3
            else:
                # 其他情况尽量接近正方形
                cols = int(count ** 0.5) + (1 if count ** 0.5 != int(count ** 0.5) else 0)
                rows = (count + cols - 1) // cols
            
            # 计算每张小图的大小
            cell_width = self.thumbnail_width
            cell_height = self.thumbnail_height
            
            # 计算总尺寸
            total_width = cols * cell_width
            total_height = rows * cell_height
            
            # 构建FFmpeg命令来拼接图片
            cmd = ['ffmpeg']
            
            # 添加所有输入文件
            for img_path in image_paths:
                cmd.extend(['-i', img_path])
            
            # 构建filter_complex - 修复版本
            filter_parts = []
            
            # 1. 缩放所有输入图片
            for i in range(count):
                filter_parts.append(f'[{i}:v]scale={cell_width}:{cell_height}[img{i}]')
            
            # 2. 创建基础画布
            filter_parts.append(f'color=black:size={total_width}x{total_height}[canvas]')
            
            # 3. 拼接所有图片到画布上
            current_output = 'canvas'
            for i in range(count):
                row = i // cols
                col = i % cols
                x = col * cell_width
                y = row * cell_height
                
                if i == 0:
                    filter_parts.append(f'[{current_output}][img{i}]overlay={x}:{y}[out{i}]')
                else:
                    filter_parts.append(f'[{current_output}][img{i}]overlay={x}:{y}[out{i}]')
                
                current_output = f'out{i}'
            
            # 4. 最终输出
            filter_parts.append(f'[{current_output}]format=yuv420p[final]')
            
            filter_complex = ';'.join(filter_parts)
            
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[final]',
                '-frames:v', '1',
                '-q:v', '2',
                '-y',
                output_path
            ])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"生成拼接缩略图: {output_path}")
                return True
            else:
                logger.error(f"拼接缩略图失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"拼接缩略图时出错: {e}")
            return False
    
    def generate_cover_image(self, video_path, cover_path):
        """生成封面图（从视频中间截取）"""
        try:
            # 获取视频时长
            duration = self.get_video_duration(video_path)
            if duration is None:
                return False
            
            # 从视频中间截取一帧作为封面
            middle_time = duration / 2
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(middle_time),
                '-vframes', '1',
                '-vf', f'scale={self.cover_width}:{self.cover_height}',
                '-q:v', '2',
                '-y',
                cover_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"生成封面图: {cover_path}")
                return True
            else:
                logger.error(f"生成封面图失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"生成封面图时出错: {e}")
            return False
    
    def get_video_duration(self, video_path):
        """获取视频时长（秒）"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            else:
                logger.error(f"获取视频时长失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"获取视频时长时出错: {e}")
            return None
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def get_conversion_info(self, ts_file_path):
        """获取转码信息"""
        if not os.path.exists(ts_file_path):
            return None
        
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                ts_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # 提取关键信息
                format_info = info.get('format', {})
                streams = info.get('streams', [])
                
                video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
                audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
                
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'video_codec': video_stream.get('codec_name', 'unknown') if video_stream else 'unknown',
                    'audio_codec': audio_stream.get('codec_name', 'unknown') if audio_stream else 'unknown',
                    'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else 'unknown'
                }
            else:
                logger.error(f"获取视频信息失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"获取视频信息时出错: {e}")
            return None

def test_ffmpeg_conversion():
    """测试FFmpeg转码功能"""
    print("测试FFmpeg转码功能...")
    
    # 模拟配置
    config = {
        'auto_convert_to_mp4': True,
        'delete_ts_after_conversion': True,
        'ffmpeg_preset': 'medium',
        'ffmpeg_crf': 23
    }
    
    converter = FFmpegConverter(config)
    
    # 检查FFmpeg
    if not converter.check_ffmpeg():
        print("❌ FFmpeg未安装或不可用")
        print("请安装FFmpeg:")
        print("Windows: 下载 https://ffmpeg.org/download.html")
        print("Linux: sudo apt install ffmpeg")
        print("macOS: brew install ffmpeg")
        return
    
    print("✅ FFmpeg可用")
    print(f"转码预设: {converter.preset}")
    print(f"CRF值: {converter.crf}")
    print(f"自动删除TS: {converter.delete_ts}")

if __name__ == "__main__":
    test_ffmpeg_conversion()
