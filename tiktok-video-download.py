"""
@author: Cesium
@desc: TikTok视频下载
@date: 2020/9/28
@note: 此处实现的是"tiktok"视频下载，不能保证适用于“抖音”
"""

import requests
import re
import datetime


h = {
    'Host': 'www.tiktok.com',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 Edg/83.0.478.37',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6'
    }

def get_long_url(short_url):
    """
    由t.co短链获取原始链接
    :param short_url: t.co短链接
    :return:
    """
    res = requests.get(url=short_url, timeout=18, proxies={'http': 'http://127.0.0.1:10809',
                                         'https': 'https://127.0.0.1:10809'})
    return res.url.replace('t.', 'www.')

def download(short_url):
    """
    获取tiktok视频，返回下载地址
    :param short_url: tiktok链接
    """
    long_url = get_long_url(short_url) if '://t.co/' in short_url else short_url
    h1 = h.copy()
    h1['Referer'] = short_url
    res = requests.get(long_url, headers=h1, proxies={'http': 'http://127.0.0.1:10809',
                                         'https': 'https://127.0.0.1:10809'})
    tik_url = re.search('"urls":\["(.+?)"', res.text).group(1)
    res1 = requests.get(tik_url, headers={'Range': 'bytes=0-'})
    file_name = str(datetime.datetime.now().strftime('%y%m%d%H%M'))+'.mp4'
    with open('.\\media\\'+file_name,'wb') as f:
        f.write(res1.content)
    return '101.200.184.98:8080/tiktok/'+file_name
