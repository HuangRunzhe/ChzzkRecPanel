# Chzzk录制程序 Web 管理面板

这是一个为Chzzk录制程序设计的现代化Web管理面板，提供直观的界面来管理录制配置和监控录制状态。

## 功能特性

- 🎯 **频道管理**: 添加、删除、预览录制频道
- ⚙️ **配置管理**: 修改录制、通知、处理等配置
- 📊 **实时监控**: 实时显示录制状态和系统信息
- 📝 **日志查看**: 查看系统运行日志
- 🎨 **现代化界面**: 响应式设计，支持移动端

## 安装依赖

首先确保已安装必要的Python包：

```bash
pip install flask flask-cors flask-socketio requests
```

## 启动方法

### 方法1: 使用启动脚本（推荐）

```bash
cd recorder
python start_web_panel.py
```

### 方法2: 直接运行

```bash
cd recorder
python web_panel.py
```

### 方法3: 自定义参数

```bash
cd recorder
python start_web_panel.py --host 0.0.0.0 --port 8080 --debug
```

## 参数说明

- `--host`: 绑定主机地址（默认: 127.0.0.1）
- `--port`: 绑定端口（默认: 8080）
- `--debug`: 启用调试模式
- `--config`: 配置文件路径（默认: config_local.json）
- `--record-list`: 频道列表文件路径（默认: record_list.txt）

## 访问界面

启动后，在浏览器中访问：

```
http://127.0.0.1:8080
```

## 使用说明

### 1. 频道管理

- **添加频道**: 点击"添加频道"按钮，输入Chzzk频道ID
- **删除频道**: 点击频道行的删除按钮
- **预览频道**: 点击预览按钮在新窗口打开频道页面

### 2. 配置管理

#### 录制配置
- **录制质量**: 选择录制质量（best/1080p/720p/480p）
- **录制间隔**: 设置检查频道状态的间隔时间
- **录制弹幕**: 是否同时录制弹幕

#### 通知配置
- **Telegram通知**: 配置Telegram Bot Token和Chat ID
- **Discord通知**: 配置Discord Bot Token和Channel ID

#### 处理配置
- **自动转换**: 是否自动将TS文件转换为MP4
- **删除TS**: 转换后是否删除原始TS文件
- **生成缩略图**: 是否生成视频缩略图
- **FFmpeg预设**: 选择FFmpeg编码预设

### 3. 实时监控

- **状态概览**: 显示总频道数、直播中频道数、录制中频道数
- **频道列表**: 实时显示频道状态和观众数
- **系统日志**: 查看系统运行日志

## 文件结构

```
recorder/
├── web_panel.py              # Web面板后端
├── start_web_panel.py        # 启动脚本
├── templates/
│   └── index.html           # 主页面模板
├── static/
│   ├── css/
│   │   └── style.css        # 样式文件
│   ├── js/
│   │   └── app.js          # JavaScript文件
│   └── img/
│       └── default-avatar.svg # 默认头像
├── config_local.json         # 配置文件
└── record_list.txt          # 频道列表文件
```

## 注意事项

1. **端口占用**: 确保8080端口未被占用，或使用`--port`参数指定其他端口
2. **配置文件**: 确保`config_local.json`文件存在且格式正确
3. **网络访问**: 如需从其他设备访问，使用`--host 0.0.0.0`
4. **权限问题**: 确保程序有读写配置文件的权限

## 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr :8080

# 使用其他端口
python start_web_panel.py --port 8081
```

### 2. 配置文件错误
- 检查`config_local.json`文件是否存在
- 验证JSON格式是否正确
- 确保文件权限正确

### 3. 频道添加失败
- 验证Chzzk频道ID是否正确
- 检查网络连接
- 查看浏览器控制台错误信息

## 开发模式

启用调试模式以获得更详细的日志：

```bash
python start_web_panel.py --debug
```

这将启用：
- 详细的错误信息
- 自动重载功能
- 调试日志输出
