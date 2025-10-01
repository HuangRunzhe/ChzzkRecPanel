#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chzzk弹幕录制模块
通过WebSocket连接获取实时弹幕
"""

import asyncio
import websockets
import json
import logging
import os
import datetime
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ChatRecorder:
    def __init__(self, channel_id: str, output_dir: str):
        self.channel_id = channel_id
        self.output_dir = output_dir
        self.websocket = None
        self.running = False
        self.chat_file = None
        self.chat_thread = None
        
    def start(self):
        """启动弹幕录制"""
        try:
            # 创建弹幕文件
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            chat_filename = f"chat_{self.channel_id}_{timestamp}.jsonl"
            self.chat_file_path = os.path.join(self.output_dir, chat_filename)
            
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 启动弹幕录制线程
            self.running = True
            self.chat_thread = threading.Thread(target=self._run_chat_recorder)
            self.chat_thread.daemon = True
            self.chat_thread.start()
            
            logger.info(f"Chat recording started for channel {self.channel_id}")
            logger.info(f"Chat file: {self.chat_file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start chat recording: {e}")
            return False
    
    def stop(self):
        """停止弹幕录制"""
        try:
            self.running = False
            if self.websocket:
                asyncio.run(self._close_websocket())
            if self.chat_thread:
                self.chat_thread.join(timeout=5)
            if self.chat_file:
                self.chat_file.close()
            logger.info(f"Chat recording stopped for channel {self.channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop chat recording: {e}")
            return False
    
    def _run_chat_recorder(self):
        """运行弹幕录制（在线程中）"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步弹幕录制
            loop.run_until_complete(self._record_chat())
            
        except Exception as e:
            logger.error(f"Chat recorder thread error: {e}")
        finally:
            if self.chat_file:
                self.chat_file.close()
    
    async def _record_chat(self):
        """异步录制弹幕"""
        try:
            # 打开弹幕文件
            self.chat_file = open(self.chat_file_path, 'w', encoding='utf-8')
            
            # 连接WebSocket
            ws_url = f"wss://kr-ss1.chat.naver.com/chat"
            self.websocket = await websockets.connect(ws_url)
            
            # 发送认证消息
            auth_message = {
                "cmd": "connect",
                "bdy": {
                    "uid": f"chat_recorder_{self.channel_id}",
                    "sid": self.channel_id,
                    "svcId": "game",
                    "ver": "2"
                }
            }
            
            await self.websocket.send(json.dumps(auth_message))
            logger.info(f"Connected to chat WebSocket for channel {self.channel_id}")
            
            # 监听弹幕消息
            async for message in self.websocket:
                if not self.running:
                    break
                    
                try:
                    data = json.loads(message)
                    await self._process_chat_message(data)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Error processing chat message: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Chat recording error: {e}")
        finally:
            await self._close_websocket()
    
    async def _process_chat_message(self, data: Dict):
        """处理弹幕消息"""
        try:
            if not self.chat_file:
                return
                
            # 提取弹幕信息
            chat_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'raw_data': data
            }
            
            # 根据消息类型处理
            if data.get('cmd') == 'message':
                bdy = data.get('bdy', {})
                chat_data.update({
                    'type': 'message',
                    'user_id': bdy.get('uid', ''),
                    'nickname': bdy.get('nick', ''),
                    'message': bdy.get('msg', ''),
                    'profile_image': bdy.get('profile', ''),
                    'badge': bdy.get('badge', ''),
                    'donation': bdy.get('donation', 0)
                })
            elif data.get('cmd') == 'donation':
                bdy = data.get('bdy', {})
                chat_data.update({
                    'type': 'donation',
                    'user_id': bdy.get('uid', ''),
                    'nickname': bdy.get('nick', ''),
                    'amount': bdy.get('amount', 0),
                    'message': bdy.get('msg', ''),
                    'currency': bdy.get('currency', 'KRW')
                })
            elif data.get('cmd') == 'enter':
                bdy = data.get('bdy', {})
                chat_data.update({
                    'type': 'enter',
                    'user_id': bdy.get('uid', ''),
                    'nickname': bdy.get('nick', ''),
                    'profile_image': bdy.get('profile', '')
                })
            elif data.get('cmd') == 'leave':
                bdy = data.get('bdy', {})
                chat_data.update({
                    'type': 'leave',
                    'user_id': bdy.get('uid', ''),
                    'nickname': bdy.get('nick', '')
                })
            else:
                # 其他类型的消息
                chat_data['type'] = data.get('cmd', 'unknown')
            
            # 写入文件
            self.chat_file.write(json.dumps(chat_data, ensure_ascii=False) + '\n')
            self.chat_file.flush()
            
        except Exception as e:
            logger.warning(f"Error processing chat message: {e}")
    
    async def _close_websocket(self):
        """关闭WebSocket连接"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
        except Exception as e:
            logger.warning(f"Error closing WebSocket: {e}")
    
    def get_chat_file_path(self) -> Optional[str]:
        """获取弹幕文件路径"""
        return self.chat_file_path if hasattr(self, 'chat_file_path') else None
