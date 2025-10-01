# Recorder - Chzzk Recording Station

Local recording system for monitoring and recording Chzzk live streams.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start recording system
python auto_restart.py
```

## 📁 Project Structure

```
recorder/
├── auto_restart.py           # ✅ 自动重启管理器（推荐启动方式）
├── recorder_main.py          # ✅ 录制端主程序（支持API集成）
├── api_client.py             # ✅ API客户端
├── telegram_notifier.py      # ✅ Telegram通知
├── ffmpeg_converter.py       # ✅ 视频转换
├── config_local.json         # ✅ 本地配置文件
├── record_list.txt           # ✅ 本地频道列表
├── api/
│   └── chzzk.py             # ✅ Chzzk API接口
├── bots/
│   └── discord_bot.py        # ✅ Discord机器人
├── multi_chzzk_recorder.py   # ❌ 已过时
├── system_monitor.py         # ❌ 已过时
└── requirements.txt          # ✅ Python依赖
```

## 🔧 Configuration

Edit `config.json` to configure the recording system:

```json
{
  "nid_aut": "your_nid_aut_cookie",
  "nid_ses": "your_nid_ses_cookie",
  "recording_save_root_dir": "download/",
  "quality": "720p",
  "use_discord_bot": true,
  "discord_bot_token": "your_discord_bot_token",
  "discord_channel_id": "your_channel_id",
  "use_telegram_bot": true,
  "telegram_bot_token": "your_telegram_bot_token",
  "telegram_chat_id": "your_chat_id"
}
```

## 📋 Features

### Core Recording
- **Auto Detection** - Automatically detects live streams
- **Quality Control** - Multiple resolution support (480p, 720p, 1080p)
- **File Management** - Automatic file naming and organization
- **Error Recovery** - Automatic retry on failures

### Auto Restart System
- **Process Monitoring** - Monitors recording processes
- **Crash Recovery** - Automatically restarts crashed processes
- **Rate Limiting** - Prevents excessive restarts
- **Health Checks** - System resource monitoring

### Notifications
- **Discord Integration** - Rich embed notifications
- **Telegram Integration** - HTML formatted messages
- **Daily Reports** - Automated daily statistics
- **Status Updates** - Recording start/end notifications

### Video Processing
- **Format Conversion** - Automatic TS to MP4 conversion
- **Thumbnail Generation** - Multiple thumbnail creation
- **Cover Images** - Automatic cover image generation
- **File Cleanup** - Automatic cleanup of temporary files

## 🚀 Usage

### Start Recording System
```bash
python auto_restart.py
```

This will:
- Start the main recording process
- Start system monitoring
- Enable auto-restart functionality
- Send startup notifications
- Send daily summary reports

### Monitor Channels
Add channel IDs to `record_list.txt`:
```
7c992b6ba76eb14f84168df1da6ccdcb
bc60b2a4493fabba7c41f4480fc26dd2
```

### Check System Status
The system automatically monitors:
- CPU usage
- Memory usage
- Disk space
- Network connectivity
- Process health

## 📊 Daily Summary

The system automatically sends daily summary reports at 9 AM and 6 PM:

```
📊 September 19, 2024 Daily Summary

🎯 Recordings: 15 total, 14 successful (93.3%)
👥 Streamers: 8 active
⏱️ Duration: 24.5 hours
💾 Storage: 45.2 GB

---
📅 Generated: 15:30:00
```

## 🛠️ Development

### Manual Recording
```bash
python multi_chzzk_recorder.py
```

### System Monitoring Only
```bash
python system_monitor.py
```

### Test Notifications
```bash
python telegram_notifier.py
```

## 📦 Dependencies

- **streamlink** - Stream recording
- **disnake** - Discord bot library
- **pyzmq** - Inter-process communication
- **requests** - HTTP requests
- **psutil** - System monitoring
- **python-telegram-bot** - Telegram integration
- **schedule** - Task scheduling

## 🌐 Network Requirements

- **Outbound HTTPS** - For API calls and notifications
- **Stream Access** - For recording live streams
- **Discord API** - For Discord notifications
- **Telegram API** - For Telegram notifications

## 🚨 Troubleshooting

### Common Issues

1. **Cookie Expired**
   - Update `nid_aut` and `nid_ses` in config.json
   - Get fresh cookies from browser

2. **Recording Failed**
   - Check network connectivity
   - Verify stream quality settings
   - Ensure sufficient disk space

3. **Notifications Not Working**
   - Check bot tokens and channel IDs
   - Verify network connectivity
   - Check bot permissions

4. **Process Crashes**
   - Check logs in `logs/` directory
   - Verify all dependencies are installed
   - Check system resources

### Logs
- **Auto Restart**: `logs/auto_restart.log`
- **Recording**: Console output
- **System Monitor**: Console output

## 🔧 Advanced Configuration

### Custom Quality Settings
```json
{
  "quality": "720p",
  "ffmpeg_preset": "medium",
  "ffmpeg_crf": 23
}
```

### Notification Settings
```json
{
  "use_discord_bot": true,
  "use_telegram_bot": true,
  "daily_summary_times": ["09:00", "18:00"]
}
```

### File Management
```json
{
  "auto_convert_to_mp4": true,
  "delete_ts_after_conversion": true,
  "generate_thumbnails": true,
  "thumbnail_count": 3
}
```
