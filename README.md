# Multi Chzzk Recorder

一个功能强大的Chzzk直播录制工具，支持多频道监控、自动录制、转码和通知功能。

## 🚀 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置设置**
   - 复制 `src/config/config_local.json.example` 为 `src/config/config_local.json`
   - 编辑配置文件，填入你的Chzzk认证信息和其他设置

3. **启动录制器**
   ```bash
   python main.py --mode recorder
   ```

4. **启动Web管理面板**
   ```bash
   python main.py --mode web
   ```
   然后访问 http://localhost:5000

## 📋 功能特性

- ✅ 多频道同时监控录制
- ✅ 自动检测直播状态
- ✅ 支持多种录制质量
- ✅ 自动转码为MP4格式
- ✅ 生成缩略图和封面
- ✅ Telegram/Discord通知
- ✅ Web管理面板
- ✅ 中英双语支持
- ✅ 聊天记录录制

## ⚙️ 配置说明

### 认证信息
- `nid_aut`: Chzzk认证token
- `nid_ses`: Chzzk会话token

### 录制设置
- `quality`: 录制质量 (best, worst, 720p, 480p等)
- `recording_save_root_dir`: 录制文件保存目录
- `record_chat`: 是否录制聊天

### 通知设置
- `use_telegram_bot`: 启用Telegram通知
- `telegram_bot_token`: Telegram Bot Token
- `telegram_chat_id`: Telegram Chat ID
- `use_discord_bot`: 启用Discord通知
- `discord_bot_token`: Discord Bot Token
- `discord_channel_id`: Discord频道ID

## 📁 项目结构

```
recorder-release/
├── main.py                 # 主入口文件
├── requirements.txt        # Python依赖
├── src/
│   ├── core/              # 核心录制逻辑
│   ├── api/               # API接口
│   ├── utils/             # 工具模块
│   ├── web/               # Web管理面板
│   └── config/            # 配置文件
├── docs/                  # 文档
└── examples/              # 示例脚本
```

## 🔧 使用说明

### 添加录制频道
1. 启动Web面板
2. 在"频道管理"中添加频道
3. 输入频道ID或用户名
4. 保存设置

### 手动转换
```bash
python examples/manual_convert.py
```

### 更新Cookie
```bash
python examples/update_cookies.py
```

## 📝 注意事项

- 首次使用需要配置Chzzk认证信息
- 确保有足够的磁盘空间用于录制
- 建议定期清理旧的录制文件
- Web面板默认运行在5000端口

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License