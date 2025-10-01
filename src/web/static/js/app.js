// Web管理面板JavaScript
class RecorderPanel {
    constructor() {
        this.socket = null;
        this.channels = [];
        this.config = {};
        this.init();
    }

    init() {
        // 初始化国际化
        initLanguage();
        
        this.initSocket();
        this.loadData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateStatusIndicator(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateStatusIndicator(false);
        });

        this.socket.on('status_update', (data) => {
            this.updateChannels(data.channels);
            this.updateLastUpdateTime(data.timestamp);
        });
    }

    async loadData() {
        try {
            await Promise.all([
                this.loadChannels(),
                this.loadConfig(),
                this.loadStatus(),
                this.loadLogs()
            ]);
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showAlert('加载数据失败', 'danger');
        }
    }

    async loadChannels() {
        try {
            const response = await fetch('/api/channels');
            const channels = await response.json();
            this.channels = channels;
            this.renderChannels();
            this.updateChannelStats();
        } catch (error) {
            console.error('Failed to load channels:', error);
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.config = config;
            this.populateConfigForm();
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            this.updateStatusCards(status);
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs');
            const data = await response.json();
            this.renderLogs(data.logs);
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }

    renderChannels() {
        const tbody = document.getElementById('channels-table');
        tbody.innerHTML = '';

        if (this.channels.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="bi bi-info-circle"></i>
                        ${t('channels.no_channels')}
                    </td>
                </tr>
            `;
            return;
        }

        this.channels.forEach(channel => {
            const row = this.createChannelRow(channel);
            tbody.appendChild(row);
        });
    }

    createChannelRow(channel) {
        const row = document.createElement('tr');
        
        const statusClass = channel.is_live ? 'status-live' : 'status-offline';
        const statusText = channel.is_live ? t('channels.live') : t('channels.offline');
        const viewerCount = channel.viewer_count ? channel.viewer_count.toLocaleString() : '0';
        
        row.innerHTML = `
            <td>
                <img src="${channel.channel_image || '/static/img/default-avatar.svg'}" 
                     class="channel-avatar" 
                     alt="频道头像"
                     onerror="this.src='/static/img/default-avatar.svg'">
            </td>
            <td>
                <div class="fw-medium">${channel.channel_name}</div>
                ${channel.live_title ? `<small class="text-muted">${channel.live_title}</small>` : ''}
            </td>
            <td>
                <code class="small">${channel.channel_id}</code>
            </td>
            <td>
                <span class="badge ${statusClass}">${statusText}</span>
            </td>
            <td>
                <span class="text-muted">${viewerCount}</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" 
                            onclick="previewChannel('${channel.channel_id}')"
                            title="${t('channels.preview')}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-danger" 
                            onclick="deleteChannel('${channel.channel_id}')"
                            title="${t('channels.delete')}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }

    updateChannelStats() {
        const totalChannels = this.channels.length;
        const liveChannels = this.channels.filter(ch => ch.is_live).length;
        
        document.getElementById('total-channels').textContent = totalChannels;
        document.getElementById('live-channels').textContent = liveChannels;
    }

    updateStatusCards(status) {
        document.getElementById('total-channels').textContent = status.total_channels || 0;
        document.getElementById('live-channels').textContent = status.live_channels || 0;
        document.getElementById('recording-channels').textContent = status.recording_channels || 0;
    }

    updateStatusIndicator(connected) {
        const indicator = document.getElementById('status-indicator');
        if (connected) {
            indicator.innerHTML = `<i class="bi bi-circle-fill text-success"></i> <span data-i18n="nav.status.running">System Running</span>`;
        } else {
            indicator.innerHTML = `<i class="bi bi-circle-fill text-danger"></i> <span data-i18n="nav.status.disconnected">Disconnected</span>`;
        }
        // 重新应用国际化
        changeLanguage(currentLanguage);
    }

    updateLastUpdateTime(timestamp) {
        const lastUpdate = document.getElementById('last-update');
        if (timestamp) {
            const date = new Date(timestamp);
            lastUpdate.textContent = date.toLocaleTimeString();
        }
    }

    populateConfigForm() {
        // 录制配置
        if (this.config.recording) {
            document.getElementById('recording-quality').value = this.config.recording.quality || 'best';
            document.getElementById('recording-interval').value = this.config.recording.interval || 600;
            document.getElementById('recording-save-dir').value = this.config.recording.recording_save_root_dir || 'download/';
            document.getElementById('file-name-format').value = this.config.recording.file_name_format || '{stream_started}.ts';
            document.getElementById('vod-name-format').value = this.config.recording.vod_name_format || '[{username}]{stream_started}_{escaped_title}.mp4';
            document.getElementById('time-format').value = this.config.recording.time_format || '%y-%m-%d';
            document.getElementById('record-chat').checked = this.config.recording.record_chat || false;
            document.getElementById('fallback-current-dir').checked = this.config.recording.fallback_to_current_dir || false;
        }

        // 通知配置
        if (this.config.notifications) {
            document.getElementById('use-telegram').checked = this.config.notifications.use_telegram_bot || false;
            document.getElementById('telegram-token').value = this.config.notifications.telegram_bot_token || '';
            document.getElementById('telegram-chat-id').value = this.config.notifications.telegram_chat_id || '';
            document.getElementById('use-discord').checked = this.config.notifications.use_discord_bot || false;
            document.getElementById('discord-token').value = this.config.notifications.discord_bot_token || '';
            document.getElementById('discord-channel-id').value = this.config.notifications.discord_channel_id || '';
        }

        // 处理配置
        if (this.config.processing) {
            document.getElementById('auto-convert').checked = this.config.processing.auto_convert_to_mp4 || false;
            document.getElementById('delete-ts').checked = this.config.processing.delete_ts_after_conversion || false;
            document.getElementById('generate-thumbnails').checked = this.config.processing.generate_thumbnails || false;
            document.getElementById('ffmpeg-preset').value = this.config.processing.ffmpeg_preset || 'medium';
            document.getElementById('ffmpeg-crf').value = this.config.processing.ffmpeg_crf || 23;
            document.getElementById('thumbnail-count').value = this.config.processing.thumbnail_count || 6;
            document.getElementById('thumbnail-width').value = this.config.processing.thumbnail_width || 320;
            document.getElementById('thumbnail-height').value = this.config.processing.thumbnail_height || 180;
            document.getElementById('cover-width').value = this.config.processing.cover_image_width || 1280;
            document.getElementById('cover-height').value = this.config.processing.cover_image_height || 720;
        }

        // 系统配置
        if (this.config.system) {
            document.getElementById('zmq-port').value = this.config.system.zmq_port || 5555;
            document.getElementById('check-interval').value = this.config.system.check_interval || 120;
            document.getElementById('max-restart-attempts').value = this.config.system.max_restart_attempts || 5;
            document.getElementById('restart-delay').value = this.config.system.restart_delay || 30;
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('log-container');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = `<div class="text-muted text-center">${t('logs.no_logs')}</div>`;
            return;
        }

        const logHtml = logs.map(log => {
            const logClass = this.getLogClass(log);
            return `<div class="log-entry ${logClass}">${this.escapeHtml(log)}</div>`;
        }).join('');

        container.innerHTML = logHtml;
        container.scrollTop = container.scrollHeight;
    }

    getLogClass(log) {
        if (log.includes('ERROR') || log.includes('错误')) return 'log-error';
        if (log.includes('WARNING') || log.includes('警告')) return 'log-warning';
        if (log.includes('SUCCESS') || log.includes('成功')) return 'log-success';
        return 'log-info';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupEventListeners() {
        // 频道ID输入框事件
        document.getElementById('new-channel-id').addEventListener('input', (e) => {
            const channelId = e.target.value.trim();
            if (channelId.length > 10) {
                this.previewChannelInfo(channelId);
            } else {
                document.getElementById('channel-preview').style.display = 'none';
            }
        });
    }

    async previewChannelInfo(channelId) {
        try {
            const response = await fetch(`https://api.chzzk.naver.com/service/v1/channels/${channelId}`);
            const data = await response.json();
            
            if (data.content) {
                const content = data.content;
                document.getElementById('preview-image').src = content.channelImageUrl || '/static/img/default-avatar.png';
                document.getElementById('preview-name').textContent = content.channelName || '未知频道';
                document.getElementById('preview-id').textContent = channelId;
                document.getElementById('channel-preview').style.display = 'block';
            }
        } catch (error) {
            console.error('Failed to preview channel:', error);
            document.getElementById('channel-preview').style.display = 'none';
        }
    }

    startAutoRefresh() {
        // 每30秒刷新一次状态
        setInterval(() => {
            this.loadStatus();
        }, 30000);

        // 每60秒刷新一次日志
        setInterval(() => {
            this.loadLogs();
        }, 60000);
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.insertBefore(alertDiv, document.body.firstChild);
        
        // 5秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// 全局函数
async function addChannel() {
    const channelId = document.getElementById('new-channel-id').value.trim();
    
    if (!channelId) {
        panel.showAlert('请输入频道ID', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel_id: channelId })
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.channel_added'), 'success');
            panel.loadChannels();
            bootstrap.Modal.getInstance(document.getElementById('addChannelModal')).hide();
            document.getElementById('new-channel-id').value = '';
            document.getElementById('channel-preview').style.display = 'none';
        } else {
            panel.showAlert(result.error || t('messages.add_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to add channel:', error);
        panel.showAlert(t('messages.add_failed'), 'danger');
    }
}

async function deleteChannel(channelId) {
    if (!confirm(t('messages.channel_deleted'))) {
        return;
    }

    try {
        const response = await fetch(`/api/channels/${channelId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.channel_deleted'), 'success');
            panel.loadChannels();
        } else {
            panel.showAlert(result.error || t('messages.delete_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to delete channel:', error);
        panel.showAlert(t('messages.delete_failed'), 'danger');
    }
}

function previewChannel(channelId) {
    window.open(`https://chzzk.naver.com/live/${channelId}`, '_blank');
}

async function saveRecordingConfig() {
    const config = {
        recording: {
            quality: document.getElementById('recording-quality').value,
            interval: parseInt(document.getElementById('recording-interval').value),
            recording_save_root_dir: document.getElementById('recording-save-dir').value,
            file_name_format: document.getElementById('file-name-format').value,
            vod_name_format: document.getElementById('vod-name-format').value,
            time_format: document.getElementById('time-format').value,
            record_chat: document.getElementById('record-chat').checked,
            fallback_to_current_dir: document.getElementById('fallback-current-dir').checked
        }
    };

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.config_saved'), 'success');
        } else {
            panel.showAlert(result.error || t('messages.save_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to save recording config:', error);
        panel.showAlert(t('messages.save_failed'), 'danger');
    }
}

async function saveNotificationConfig() {
    const config = {
        notifications: {
            use_telegram_bot: document.getElementById('use-telegram').checked,
            telegram_bot_token: document.getElementById('telegram-token').value,
            telegram_chat_id: document.getElementById('telegram-chat-id').value,
            use_discord_bot: document.getElementById('use-discord').checked,
            discord_bot_token: document.getElementById('discord-token').value,
            discord_channel_id: document.getElementById('discord-channel-id').value
        }
    };

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.config_saved'), 'success');
        } else {
            panel.showAlert(result.error || t('messages.save_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to save notification config:', error);
        panel.showAlert(t('messages.save_failed'), 'danger');
    }
}

async function saveProcessingConfig() {
    const config = {
        processing: {
            auto_convert_to_mp4: document.getElementById('auto-convert').checked,
            delete_ts_after_conversion: document.getElementById('delete-ts').checked,
            generate_thumbnails: document.getElementById('generate-thumbnails').checked,
            ffmpeg_preset: document.getElementById('ffmpeg-preset').value,
            ffmpeg_crf: parseInt(document.getElementById('ffmpeg-crf').value),
            thumbnail_count: parseInt(document.getElementById('thumbnail-count').value),
            thumbnail_width: parseInt(document.getElementById('thumbnail-width').value),
            thumbnail_height: parseInt(document.getElementById('thumbnail-height').value),
            cover_image_width: parseInt(document.getElementById('cover-width').value),
            cover_image_height: parseInt(document.getElementById('cover-height').value)
        }
    };

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.config_saved'), 'success');
        } else {
            panel.showAlert(result.error || t('messages.save_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to save processing config:', error);
        panel.showAlert(t('messages.save_failed'), 'danger');
    }
}

async function saveSystemConfig() {
    const config = {
        system: {
            zmq_port: parseInt(document.getElementById('zmq-port').value),
            check_interval: parseInt(document.getElementById('check-interval').value),
            max_restart_attempts: parseInt(document.getElementById('max-restart-attempts').value),
            restart_delay: parseInt(document.getElementById('restart-delay').value)
        }
    };

    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();
        
        if (result.success) {
            panel.showAlert(t('messages.config_saved'), 'success');
        } else {
            panel.showAlert(result.error || t('messages.save_failed'), 'danger');
        }
    } catch (error) {
        console.error('Failed to save system config:', error);
        panel.showAlert(t('messages.save_failed'), 'danger');
    }
}

function refreshLogs() {
    panel.loadLogs();
}

// 初始化应用
let panel;
document.addEventListener('DOMContentLoaded', () => {
    panel = new RecorderPanel();
});
