# Cookie 管理指南

## 问题说明

Chzzk 的 Cookie 会定期失效，导致录制器无法正常工作。主要原因包括：

1. **Cookie 生命周期短** - `NID_SES` cookie 通常只有几小时到几天的有效期
2. **频繁的 API 调用** - 每分钟检查频道状态会加速 cookie 消耗
3. **IP 变化** - 服务器 IP 变化可能导致 cookie 失效
4. **浏览器会话过期** - 原始获取 cookie 的浏览器会话过期

## 解决方案

### 1. 自动 Cookie 检查

录制器现在会自动检查 Cookie 有效性：
- 每 5 分钟检查一次 Cookie 状态
- 如果 Cookie 失效，会跳过本次检查并显示警告
- 不会中断录制进程

### 2. Cookie 更新工具

使用 `update_cookies.py` 脚本快速更新 Cookie：

```bash
python update_cookies.py
```

### 3. 手动获取新 Cookie

#### 步骤 1: 打开浏览器
访问 https://chzzk.naver.com

#### 步骤 2: 登录账号
使用你的 Chzzk 账号登录

#### 步骤 3: 打开开发者工具
按 `F12` 或右键选择"检查元素"

#### 步骤 4: 找到 Cookie
1. 切换到 `Application` 标签（Chrome）或 `存储` 标签（Firefox）
2. 在左侧找到 `Cookies` -> `https://chzzk.naver.com`
3. 找到以下两个 Cookie：
   - `NID_AUT`
   - `NID_SES`

#### 步骤 5: 复制 Cookie 值
复制这两个 Cookie 的值（不是名称）

#### 步骤 6: 更新配置文件
编辑 `config_local.json` 文件：

```json
{
  "recording": {
    "nid_aut": "你的_NID_AUT_值",
    "nid_ses": "你的_NID_SES_值"
  }
}
```

## 预防措施

### 1. 减少检查频率
在 `config_local.json` 中增加检查间隔：

```json
{
  "recording": {
    "interval": 300  // 5分钟检查一次，而不是1分钟
  }
}
```

### 2. 使用稳定的网络环境
- 避免频繁更换 IP 地址
- 使用固定的服务器环境

### 3. 定期更新 Cookie
- 建议每周更新一次 Cookie
- 在录制器显示 Cookie 失效警告时及时更新

## 故障排除

### Cookie 仍然失效
1. 确认 Cookie 值复制正确（没有多余的空格）
2. 确认浏览器已登录 Chzzk
3. 尝试清除浏览器缓存后重新获取 Cookie

### 录制器无法启动
1. 检查 `config_local.json` 文件格式是否正确
2. 确认 Cookie 值不为空
3. 查看日志文件中的具体错误信息

### API 调用失败
1. 检查网络连接
2. 确认 Chzzk 服务是否正常
3. 尝试手动访问 Chzzk API 端点

## 日志监控

录制器会记录 Cookie 相关的事件：

```
INFO - Cookie验证成功
WARNING - Cookie可能已过期 (HTTP 500)
ERROR - Cookie配置缺失
ERROR - Cookie已失效，跳过本次检查
```

定期检查日志文件，及时发现 Cookie 问题。
