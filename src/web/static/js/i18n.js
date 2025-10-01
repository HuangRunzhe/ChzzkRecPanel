// 国际化支持
const i18n = {
    en: {
        title: "Chzzk Recorder Management Panel",
        nav: {
            title: "Chzzk Recorder Management Panel",
            status: {
                running: "System Running",
                disconnected: "Disconnected"
            }
        },
        stats: {
            total_channels: "Total Channels",
            live_channels: "Live Channels", 
            recording_channels: "Recording",
            last_update: "Last Update"
        },
        channels: {
            title: "Channel Management",
            add: "Add Channel",
            avatar: "Avatar",
            name: "Channel Name",
            id: "Channel ID",
            status: "Status",
            viewers: "Viewers",
            actions: "Actions",
            live: "Live",
            offline: "Offline",
            recording: "Recording",
            no_channels: "No channels found. Click 'Add Channel' to start recording."
        },
        config: {
            title: "Configuration Management",
            recording: {
                title: "Recording Settings",
                quality: "Recording Quality",
                quality_best: "Best Quality",
                interval: "Check Interval (seconds)",
                save_dir: "Save Directory",
                file_format: "File Name Format",
                file_format_help: "Available variables: {stream_started}, {username}, {escaped_title}",
                vod_format: "VOD Name Format",
                time_format: "Time Format",
                time_format_help: "Python strftime format",
                record_chat: "Record Chat Messages",
                fallback_dir: "Fallback to Current Directory"
            },
            notifications: {
                title: "Notification Settings",
                use_telegram: "Enable Telegram Notifications",
                telegram_token: "Telegram Bot Token",
                telegram_chat_id: "Telegram Chat ID",
                use_discord: "Enable Discord Notifications",
                discord_token: "Discord Bot Token",
                discord_channel_id: "Discord Channel ID"
            },
            processing: {
                title: "Processing Settings",
                auto_convert: "Auto Convert to MP4",
                delete_ts: "Delete TS After Conversion",
                generate_thumbnails: "Generate Thumbnails",
                ffmpeg_preset: "FFmpeg Preset",
                ffmpeg_crf: "FFmpeg CRF",
                ffmpeg_crf_help: "Lower = better quality, higher = smaller file",
                thumbnail_count: "Thumbnail Count",
                thumbnail_width: "Thumbnail Width",
                thumbnail_height: "Thumbnail Height",
                cover_width: "Cover Width",
                cover_height: "Cover Height"
            },
            system: {
                title: "System Settings",
                zmq_port: "ZMQ Port",
                check_interval: "Check Interval (seconds)",
                max_restart_attempts: "Max Restart Attempts",
                restart_delay: "Restart Delay (seconds)"
            }
        },
        logs: {
            title: "System Logs",
            refresh: "Refresh",
            loading: "Loading logs...",
            no_logs: "No logs available"
        },
        modal: {
            add_channel: {
                title: "Add Channel",
                channel_id: "Channel ID",
                help: "Get Channel ID from Chzzk channel page URL"
            }
        },
        common: {
            save: "Save",
            cancel: "Cancel",
            add: "Add",
            delete: "Delete",
            preview: "Preview",
            success: "Success",
            error: "Error",
            warning: "Warning",
            info: "Info"
        },
        messages: {
            channel_added: "Channel added successfully",
            channel_deleted: "Channel deleted successfully",
            config_saved: "Configuration saved successfully",
            invalid_channel_id: "Invalid channel ID",
            channel_exists: "Channel already exists",
            add_failed: "Failed to add channel",
            delete_failed: "Failed to delete channel",
            save_failed: "Failed to save configuration",
            load_failed: "Failed to load data"
        }
    },
    zh: {
        title: "Chzzk录制程序管理面板",
        nav: {
            title: "Chzzk录制管理面板",
            status: {
                running: "系统运行中",
                disconnected: "连接断开"
            }
        },
        stats: {
            total_channels: "总频道数",
            live_channels: "直播中",
            recording_channels: "录制中",
            last_update: "最后更新"
        },
        channels: {
            title: "频道管理",
            add: "添加频道",
            avatar: "头像",
            name: "频道名称",
            id: "频道ID",
            status: "状态",
            viewers: "观众数",
            actions: "操作",
            live: "直播中",
            offline: "离线",
            recording: "录制中",
            no_channels: "暂无频道，点击'添加频道'开始录制"
        },
        config: {
            title: "配置管理",
            recording: {
                title: "录制设置",
                quality: "录制质量",
                quality_best: "最佳质量",
                interval: "检查间隔（秒）",
                save_dir: "保存目录",
                file_format: "文件名格式",
                file_format_help: "可用变量: {stream_started}, {username}, {escaped_title}",
                vod_format: "录播名称格式",
                time_format: "时间格式",
                time_format_help: "Python strftime格式",
                record_chat: "录制弹幕消息",
                fallback_dir: "回退到当前目录"
            },
            notifications: {
                title: "通知设置",
                use_telegram: "启用Telegram通知",
                telegram_token: "Telegram Bot Token",
                telegram_chat_id: "Telegram Chat ID",
                use_discord: "启用Discord通知",
                discord_token: "Discord Bot Token",
                discord_channel_id: "Discord Channel ID"
            },
            processing: {
                title: "处理设置",
                auto_convert: "自动转换为MP4",
                delete_ts: "转换后删除TS文件",
                generate_thumbnails: "生成缩略图",
                ffmpeg_preset: "FFmpeg预设",
                ffmpeg_crf: "FFmpeg CRF",
                ffmpeg_crf_help: "数值越小质量越好，数值越大文件越小",
                thumbnail_count: "缩略图数量",
                thumbnail_width: "缩略图宽度",
                thumbnail_height: "缩略图高度",
                cover_width: "封面宽度",
                cover_height: "封面高度"
            },
            system: {
                title: "系统设置",
                zmq_port: "ZMQ端口",
                check_interval: "检查间隔（秒）",
                max_restart_attempts: "最大重启尝试次数",
                restart_delay: "重启延迟（秒）"
            }
        },
        logs: {
            title: "系统日志",
            refresh: "刷新",
            loading: "正在加载日志...",
            no_logs: "暂无日志"
        },
        modal: {
            add_channel: {
                title: "添加频道",
                channel_id: "频道ID",
                help: "从Chzzk频道页面URL中获取频道ID"
            }
        },
        common: {
            save: "保存",
            cancel: "取消",
            add: "添加",
            delete: "删除",
            preview: "预览",
            success: "成功",
            error: "错误",
            warning: "警告",
            info: "信息"
        },
        messages: {
            channel_added: "频道添加成功",
            channel_deleted: "频道删除成功",
            config_saved: "配置保存成功",
            invalid_channel_id: "无效的频道ID",
            channel_exists: "频道已存在",
            add_failed: "添加频道失败",
            delete_failed: "删除频道失败",
            save_failed: "保存配置失败",
            load_failed: "加载数据失败"
        }
    }
};

// 当前语言
let currentLanguage = 'en';

// 切换语言
function changeLanguage(lang) {
    currentLanguage = lang;
    document.getElementById('current-lang').textContent = lang.toUpperCase();
    
    // 更新所有带有data-i18n属性的元素
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const text = getNestedValue(i18n[currentLanguage], key);
        if (text) {
            if (element.tagName === 'INPUT' && element.type === 'text') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        }
    });
    
    // 更新页面标题
    document.title = i18n[currentLanguage].title;
    
    // 保存语言偏好
    localStorage.setItem('language', lang);
}

// 获取嵌套对象的值
function getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current && current[key], obj);
}

// 获取翻译文本
function t(key) {
    return getNestedValue(i18n[currentLanguage], key) || key;
}

// 初始化语言
function initLanguage() {
    const savedLang = localStorage.getItem('language') || 'en';
    changeLanguage(savedLang);
}
