import requests
import json
import logging
import re

from typing import Union, Dict, TypedDict, List
from fake_useragent import UserAgent

REQUEST_TIMEOUT = 15
ua = UserAgent()
request_header = {"User-Agent": ua.chrome}
logger = logging.getLogger(__name__)


class ChzzkChannel(TypedDict):
    channelId: str
    channelName: str
    channelImageUrl: str
    openLive: bool


class ChzzkStream(TypedDict):
    liveTitle: str
    liveImageUrl: str
    openDate: str
    adult: bool


class ChzzkVideo(TypedDict):
    videoTitle: str
    publishDate: str
    thumbnailImageUrl: str
    duration: int
    channel: Dict[str, Union[str, bool]]
    liveOpenDate: str


class ChzzkAPI:
    def __init__(self, nid_aut: str, nid_ses: str):
        self._cookies = {'NID_AUT': nid_aut, 'NID_SES': nid_ses}

    def get_channel_info(self, channel_id: str) -> Union[ChzzkChannel, None]:
        """Get channel info from chzzk API.
        :param channel_id: Channel ID.
        :return: Channel info dict if channel exists, None otherwise."""
        with requests.get(f'https://api.chzzk.naver.com/service/v1/channels/{channel_id}',
                          headers=request_header, cookies=self._cookies, timeout=REQUEST_TIMEOUT) as r:
            try:
                # 检查cookie是否过期
                if 'expired' in str(r.cookies):
                    logger.error(f'Cookies have expired for channel {channel_id}')
                    logger.error('Please update your NID_AUT and NID_SES cookies in config.json')
                    return None
                
                r.raise_for_status()
                data = json.loads(r.text)['content']

                return data
            except requests.exceptions.HTTPError:
                logger.error(f'HTTP Error while getting channel {channel_id}')
                logger.error(f'HTTP Status code {r.status_code}')
                if r.status_code == 500:
                    logger.error('This might be due to expired cookies. Please check your NID_AUT and NID_SES values.')
                return None
            except requests.exceptions.Timeout:
                logger.error(f'Timeout while getting channel {channel_id}')
                return None

    def check_live(self, channel_id: str) -> (bool, Union[ChzzkStream, None]):
        # 首先尝试使用直播详情API
        try:
            with requests.get(f'https://api.chzzk.naver.com/service/v1/channels/{channel_id}/live-detail',
                              headers=request_header, cookies=self._cookies, timeout=REQUEST_TIMEOUT) as r:
                # 检查cookie是否过期
                if 'expired' in str(r.cookies):
                    logger.error(f'Cookies have expired for channel {channel_id}')
                    logger.error('Please update your NID_AUT and NID_SES cookies in config.json')
                    return False, None
                
                if r.status_code == 200:
                    data = json.loads(r.text)
                    if data['content'] is None:
                        return False, None
                    else:
                        return data['content']['status'] == 'OPEN', data['content']
                elif r.status_code == 500:
                    # 直播详情API返回500，尝试使用频道信息API作为备选
                    logger.warning(f'Live detail API returned 500 for {channel_id}, trying channel info API as fallback')
                    return self._check_live_fallback(channel_id)
                else:
                    logger.error(f'HTTP Error while checking channel {channel_id}: {r.status_code}')
                    return False, None
        except requests.exceptions.Timeout:
            logger.error(f'Timeout while checking channel {channel_id}')
            return False, None
        except Exception as e:
            logger.error(f'Error checking live status for {channel_id}: {e}')
            return False, None

    def _check_live_fallback(self, channel_id: str) -> (bool, Union[ChzzkStream, None]):
        """使用频道信息API作为备选方案检查直播状态"""
        try:
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return False, None
            
            # 检查是否在直播
            is_live = channel_info.get('openLive', False)
            if is_live:
                # 构造直播数据
                stream_data = {
                    'liveTitle': channel_info.get('liveTitle', ''),
                    'liveImageUrl': channel_info.get('liveImageUrl', ''),
                    'openDate': channel_info.get('liveOpenDate', ''),
                    'status': 'OPEN',
                    'concurrentUserCount': channel_info.get('concurrentUserCount', 0),
                    'channelName': channel_info.get('channelName', ''),
                    'channelImageUrl': channel_info.get('channelImageUrl', '')
                }
                return True, stream_data
            else:
                return False, None
        except Exception as e:
            logger.error(f'Error in fallback live check for {channel_id}: {e}')
            return False, None

    def get_video(self, video_url: str) -> Union[ChzzkVideo, None]:
        match = re.match(r'https://chzzk.naver.com/video/(\d+)', video_url)

        if not match:
            return None

        video_id = match.group(1)

        with requests.get(f'https://api.chzzk.naver.com/service/v1/videos/{video_id}',
                          headers=request_header, cookies=self._cookies, timeout=REQUEST_TIMEOUT) as r:
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error(f'HTTP Error while getting video {video_id}')
                logger.error(f'HTTP Status code {r.status_code}')
                return None
            except requests.exceptions.Timeout:
                logger.error(f'Timeout while getting video {video_id}')
                return None

            return json.loads(r.text)['content']

    def _search_channel(self, channel_name, offset=0, size=5):
        with requests.get(f'https://api.chzzk.naver.com/service/v1/search/channels?keyword={channel_name}&offset={offset}&size={size}',
                          headers=request_header, cookies=self._cookies, timeout=REQUEST_TIMEOUT) as r:
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error(f'HTTP Error while searching channel {channel_name}')
                logger.error(f'HTTP Status code {r.status_code}')
                return None
            except requests.exceptions.Timeout:
                logger.error(f'Timeout while searching channel {channel_name}')
                return None

            return json.loads(r.text)['content']['data']

    def _get_channel_by_name(self, channel_name, size=1):
        channels = self._search_channel(channel_name, size=size)

        if not channels:
            return None

        for channel in channels:
            channel = channel['channel']
            if channel['channelName'] == channel_name:
                return channel
        else:
            return None

    def get_channel_id(self, channel_name) -> str:
        channel = self._get_channel_by_name(channel_name)
        return channel['channelId'] if channel else None
