#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动转换脚本
转换TS文件为MP4并生成缩略图
"""

import os
import sys
import json
from ffmpeg_converter import FFmpegConverter

def manual_convert():
    """手动转换录制文件"""
    
    # 加载配置
    try:
        with open('config_local.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ 找不到配置文件 config_local.json")
        return False
    
    # 初始化转换器
    converter = FFmpegConverter(config['processing'])
    
    # 查找TS文件
    download_dir = config['recording']['recording_save_root_dir']
    ts_files = []
    
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            if file.endswith('.ts'):
                ts_files.append(os.path.join(root, file))
    
    if not ts_files:
        print("❌ 没有找到TS文件")
        return False
    
    print(f"找到 {len(ts_files)} 个TS文件:")
    for i, ts_file in enumerate(ts_files, 1):
        print(f"  {i}. {ts_file}")
    
    # 转换每个TS文件
    for ts_file in ts_files:
        print(f"\n{'='*60}")
        print(f"正在转换: {os.path.basename(ts_file)}")
        print(f"{'='*60}")
        
        # 生成MP4文件路径
        mp4_file = ts_file.replace('.ts', '.mp4')
        
        # 转换TS到MP4
        print("📹 转换TS到MP4...")
        print(f"   输入: {ts_file}")
        print(f"   输出: {mp4_file}")
        print("   使用快速转换模式 (copy stream)...")
        success = converter.convert_ts_to_mp4(ts_file, mp4_file)
        
        if success and os.path.exists(mp4_file):
            print(f"✅ MP4转换成功: {os.path.basename(mp4_file)}")
            
            # 生成缩略图
            print("🖼️ 生成缩略图...")
            thumbnail_success = converter.generate_video_thumbnails(mp4_file)
            
            if thumbnail_success:
                print("✅ 缩略图生成成功")
            else:
                print("❌ 缩略图生成失败")
            
            # 生成封面图
            print("🖼️ 生成封面图...")
            cover_success = converter.generate_cover_image(mp4_file)
            
            if cover_success:
                print("✅ 封面图生成成功")
            else:
                print("❌ 封面图生成失败")
            
            # 删除TS文件（如果配置了自动删除）
            if config['processing'].get('delete_ts_after_conversion', False):
                try:
                    os.remove(ts_file)
                    print(f"🗑️ 已删除TS文件: {os.path.basename(ts_file)}")
                except Exception as e:
                    print(f"⚠️ 删除TS文件失败: {e}")
            
            print(f"✅ 处理完成: {os.path.basename(mp4_file)}")
            
        else:
            print(f"❌ MP4转换失败: {os.path.basename(ts_file)}")
    
    print(f"\n{'='*60}")
    print("🎉 所有文件处理完成！")
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    print("🔄 手动转换录制文件")
    print("=" * 60)
    
    # 检查FFmpeg
    converter = FFmpegConverter({'auto_convert_to_mp4': True})
    if not converter.check_ffmpeg():
        print("❌ FFmpeg未安装或不可用")
        print("请先安装FFmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    success = manual_convert()
    
    if success:
        print("\n✅ 转换完成！")
    else:
        print("\n❌ 转换失败！")
        sys.exit(1)
