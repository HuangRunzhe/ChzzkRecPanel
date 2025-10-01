// 国际化支持
const i18n = {
    en: {
        title: "Chzzk Recorder Management Panel",
        nav: {
            title: "Chzzk Recorder Management Panel",
            dashboard: "Dashboard",
            channels: "Channels",
            config: "Configuration",
            logs: "System Logs",
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
        dashboard: {
            quick_actions: "Quick Actions",
            system_info: "System Information",
            recorder_status: "Recorder Status",
            web_panel_status: "Web Panel Status"
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
            no_channels: "No channels found. Click 'Add Channel' to start recording.",
            id_help: "Enter the channel ID or username from chzzk.naver.com",
            preview: "Preview Channel"
        },
        config: {
            title: "Configuration Management",
            auth: {
                title: "Chzzk Authentication",
                description: "Configure your Chzzk authentication tokens to enable recording.",
                nid_aut: "NID_AUT Token",
                nid_aut_help: "Get this from browser cookies when logged into chzzk.naver.com",
                nid_ses: "NID_SES Token", 
                nid_ses_help: "Get this from browser cookies when logged into chzzk.naver.com",
                save: "Save Authentication"
            },
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
                telegram: "Telegram",
                discord: "Discord",
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
            auth_saved: "Authentication saved successfully",
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
            dashboard: "仪表板",
            channels: "频道管理",
            config: "配置管理",
            logs: "系统日志",
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
        dashboard: {
            quick_actions: "快速操作",
            system_info: "系统信息",
            recorder_status: "录制器状态",
            web_panel_status: "Web面板状态"
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
            no_channels: "暂无频道，点击'添加频道'开始录制",
            id_help: "输入来自chzzk.naver.com的频道ID或用户名",
            preview: "预览频道"
        },
        config: {
            title: "配置管理",
            auth: {
                title: "Chzzk认证配置",
                description: "配置您的Chzzk认证令牌以启用录制功能。",
                nid_aut: "NID_AUT令牌",
                nid_aut_help: "从浏览器Cookie中获取，需要登录chzzk.naver.com",
                nid_ses: "NID_SES令牌",
                nid_ses_help: "从浏览器Cookie中获取，需要登录chzzk.naver.com",
                save: "保存认证信息"
            },
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
                telegram: "Telegram",
                discord: "Discord",
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
            auth_saved: "认证信息保存成功",
            invalid_channel_id: "无效的频道ID",
            channel_exists: "频道已存在",
            add_failed: "添加频道失败",
            delete_failed: "删除频道失败",
            save_failed: "保存配置失败",
            load_failed: "加载数据失败"
        }
    },
    ko: {
        title: "Chzzk 녹화 프로그램 관리 패널",
        nav: {
            title: "Chzzk 녹화 관리 패널",
            dashboard: "대시보드",
            channels: "채널 관리",
            config: "설정 관리",
            logs: "시스템 로그",
            status: {
                running: "시스템 실행 중",
                disconnected: "연결 끊김"
            }
        },
        stats: {
            total_channels: "총 채널 수",
            live_channels: "라이브 중",
            recording_channels: "녹화 중",
            last_update: "마지막 업데이트"
        },
        dashboard: {
            quick_actions: "빠른 작업",
            system_info: "시스템 정보",
            recorder_status: "녹화기 상태",
            web_panel_status: "웹 패널 상태"
        },
        channels: {
            title: "채널 관리",
            add: "채널 추가",
            avatar: "아바타",
            name: "채널 이름",
            id: "채널 ID",
            status: "상태",
            viewers: "시청자 수",
            actions: "작업",
            live: "라이브",
            offline: "오프라인",
            recording: "녹화 중",
            no_channels: "채널이 없습니다. '채널 추가'를 클릭하여 녹화를 시작하세요.",
            id_help: "chzzk.naver.com의 채널 ID 또는 사용자명을 입력하세요",
            preview: "채널 미리보기"
        },
        config: {
            title: "설정 관리",
            auth: {
                title: "Chzzk 인증 설정",
                description: "녹화 기능을 활성화하려면 Chzzk 인증 토큰을 설정하세요.",
                nid_aut: "NID_AUT 토큰",
                nid_aut_help: "chzzk.naver.com에 로그인한 상태에서 브라우저 쿠키에서 가져오세요",
                nid_ses: "NID_SES 토큰",
                nid_ses_help: "chzzk.naver.com에 로그인한 상태에서 브라우저 쿠키에서 가져오세요",
                save: "인증 정보 저장"
            },
            recording: {
                title: "녹화 설정",
                quality: "녹화 품질",
                quality_best: "최고 품질",
                interval: "확인 간격 (초)",
                save_dir: "저장 디렉토리",
                file_format: "파일명 형식",
                file_format_help: "사용 가능한 변수: {stream_started}, {username}, {escaped_title}",
                vod_format: "VOD 이름 형식",
                time_format: "시간 형식",
                time_format_help: "Python strftime 형식",
                record_chat: "채팅 메시지 녹화",
                fallback_dir: "현재 디렉토리로 폴백"
            },
            notifications: {
                title: "알림 설정",
                telegram: "텔레그램",
                discord: "디스코드",
                use_telegram: "텔레그램 알림 활성화",
                telegram_token: "텔레그램 봇 토큰",
                telegram_chat_id: "텔레그램 채팅 ID",
                use_discord: "디스코드 알림 활성화",
                discord_token: "디스코드 봇 토큰",
                discord_channel_id: "디스코드 채널 ID"
            },
            processing: {
                title: "처리 설정",
                auto_convert: "MP4로 자동 변환",
                delete_ts: "변환 후 TS 파일 삭제",
                generate_thumbnails: "썸네일 생성",
                ffmpeg_preset: "FFmpeg 프리셋",
                ffmpeg_crf: "FFmpeg CRF",
                thumbnail_count: "썸네일 개수",
                thumbnail_width: "썸네일 너비",
                thumbnail_height: "썸네일 높이",
                cover_width: "커버 이미지 너비",
                cover_height: "커버 이미지 높이"
            },
            system: {
                title: "시스템 설정",
                zmq_port: "ZMQ 포트",
                check_interval: "확인 간격 (초)",
                max_restart_attempts: "최대 재시작 시도 횟수",
                restart_delay: "재시작 지연 (초)"
            }
        },
        logs: {
            title: "시스템 로그",
            no_logs: "로그가 없습니다"
        },
        common: {
            save: "저장",
            cancel: "취소",
            delete: "삭제",
            edit: "편집",
            add: "추가",
            refresh: "새로고침",
            success: "성공",
            error: "오류",
            warning: "경고",
            info: "정보"
        },
        messages: {
            channel_added: "채널이 성공적으로 추가되었습니다",
            channel_deleted: "채널이 성공적으로 삭제되었습니다",
            config_saved: "설정이 성공적으로 저장되었습니다",
            auth_saved: "인증 정보가 성공적으로 저장되었습니다",
            invalid_channel_id: "유효하지 않은 채널 ID",
            channel_exists: "채널이 이미 존재합니다",
            add_failed: "채널 추가에 실패했습니다",
            delete_failed: "채널 삭제에 실패했습니다",
            save_failed: "설정 저장에 실패했습니다",
            load_failed: "데이터 로드에 실패했습니다"
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
