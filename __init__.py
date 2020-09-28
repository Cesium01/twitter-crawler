"""
@author: Cesium
@desc: 简单的推特爬虫
@date: 2020/9/28
@note: 需安装mysql，（若要登录）Node.js
@see: https://developer.twitter.com/en/docs
      https://dev.mysql.com/downloads/mysql/
      https://nodejs.org/zh-cn/
"""

import logging
import requests
import requests.utils
import re
import random
import json
import time
import uuid
import pymysql
import subprocess
from urllib import parse
from requests.exceptions import ProxyError


# 对应数据表的`name`字段
nananiji = ['天城莎莉','海乃琉璃','河濑诗','仓冈水巴','凉花萌','高辻丽','武田爱奈','帆风千春','宫濑玲奈']  # 某个组合
kukugumi = ['小山百代','三森铃子','富田麻帆','佐藤日向','岩田阳葵','小泉萌香','相羽爱奈','生田辉','伊藤彩沙']
Aqours = ['伊波杏树','逢田梨香子','诹访奈奈香','小宫有纱','齐藤朱夏','小林爱香','高槻加奈子','铃木爱奈','降幡爱']
all_groups = [nananiji, kukugumi, Aqours]  # 所有组合


class Gettwi:
    urls = {
        'main': 'https://twitter.com/',  # +username
        'ql': 'https://api.twitter.com/graphql/',
        'login': 'https://twitter.com/sessions',  # POST
        'timeline': 'https://api.twitter.com/2/timeline/home_latest.json'
    }
    # @see: mysql配置.md
    conn = pymysql.connect('localhost', '数据库用户名', '密码', '数据库名', port=3306, charset='utf8')
    conn.autocommit(1)  # 自动提交修改
    cursor = conn.cursor()
    # 代理（科学上网）
    ip='localhost:10809'  # 根据梯子的设置修改端口，注意不要跟其他服务端口冲突
    prx={
        'http': 'http://'+ip,
        'https': 'https://'+ip
    }
    headers = {
        'Host': 'twitter.com',
        'Connection': 'keep-alive',
        # UA，可以复制浏览器信息里的UA
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'DNT': '1',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6'
    }

    js = r"""
    const jsdom = require("jsdom");
    var JSDOM = jsdom.JSDOM;
    var document = new JSDOM(`<!DOCTYPE html><html><body><p>Text</p></body></html>`).window.document;
    %sreturn %s;}
    process.stdout.write(%s());"""

    params = {
        'include_profile_interstitial_type': '1',
        'include_blocking': '1',
        'include_blocked_by': '1',
        'include_followed_by': '1',
        'include_want_retweets': '1',
        'include_mute_edge': '1',
        'include_can_dm': '1',
        'include_can_media_tag': '1',
        'skip_status': '1',
        'cards_platform': 'Web-12',
        'include_cards': '1',
        'include_composer_source': 'true',
        'include_ext_alt_text': 'true',
        'include_reply_count': '1',
        'tweet_mode': 'extended',
        'include_entities': 'true',
        'include_user_entities': 'true',
        'include_ext_media_color': 'true',
        'include_ext_media_availability': 'true',
        'send_error_codes': 'true',
        'simple_quoted_tweets': 'true',
        'ext': 'mediaStats,highlightedLabel,cameraMoment'
    }

    def __init__(self, uname=None, pwd=None):
        self.msg = ''
        self.nid = ''
        self.s = requests.session()
        self.s.proxies = self.prx
        if uname and pwd:
            self.islogin = 1
            self.uname, self.__pwd = uname, pwd
        else:
            self.islogin = 0
        print('正在获取数据...')
        try:
            with open('.\\session.txt','r') as fs:
                session = fs.read()
            session = json.loads(session)
            self.authorization = session['auth']
            self.queryid = session['queryid']
            requests.utils.cookiejar_from_dict(session['cookies'], self.s.cookies)
        except(FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            self.__preparation('https://twitter.com')

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def print_msg(self):
        print(self.msg)

    def clear_msg(self):
        self.msg = ''

    @staticmethod
    def num16(w=32):
        """
        生成指定位数16进制数
        :param w: 位数
        :return: 16进制数的字符串
        """
        s = '0123456789abcdef'
        n = ''
        for i in range(w):
            n = n+random.choice(s)
            if i==0 and n=='0':
                n = random.choice(s.strip('0'))
        return n

    def __preparation(self, url):
        """
        初始化
        :param url:
        :return:
        """
        headers = self.headers.copy()
        headers['Upgrade-Insecure-Requests'] = '1'
        headers['Accept'] = \
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        r = self.s.get(url, headers=headers, timeout=18)
        url_js = re.search('(https://abs\.twimg\.com/responsive-web/web/main\.\w+\.js)' ,r.text).group()
        gt = re.search('gt=(\d+);', r.text).group(1)
        self.s.cookies.set('gt', gt, domain='.twitter.com')
        self.__getauth(url_js)
        self.__getsess()
        session = json.dumps({
            'auth': self.authorization,
            'queryid': self.queryid,
            'cookies': requests.utils.dict_from_cookiejar(self.s.cookies)
        })
        with open('.\\session_%s.txt'%self.uname,'w') as fs:
            fs.write(session)

    def __getauth(self, url):
        """
        获取auth
        :param url:
        :return:
        """
        headers = self.headers.copy()
        headers.update({
            'Host': 'abs.twimg.com',
            'Origin': 'https://twitter.com',
            'Referer': 'https://twitter.com/'
        })
        r = self.s.get(url, headers=headers, timeout=18)
        self.queryid = re.search('"([^"]+?)",operationName:"UserByScreenName', r.text).group(1)
        self.authorization = re.search('(AAAAAAAA.+?)"', r.text).group(1)
        # self.s.cookies.set('ct0', self.num16(), domain='.twitter.com')

    def __getsess(self):
        headers = self.headers.copy()
        headers['Referer'] = 'https://twitter.com/'
        ijs = self.s.get(url=self.urls['main']+'i/js_inst?c_name=ui_metrics', timeout=18).text
        if self.islogin:
            self.__login(ijs)

    def __login(self, ijs):
        """
        登录（可选），请勿直接调用
        此处调用了Node.js
        :param ijs: __getsess方法中获取的js文本
        :return:
        """
        func = re.search('(var.+?)var inputs;',ijs,re.S).group(1)
        name = re.search('var (\w+) =',func).group(1)
        var = re.search('(\w+) = "exception',func).group(1)
        js = self.js % (func, var, name)
        result = subprocess.check_output(
            ["node", "-e", js], stdin=subprocess.PIPE, stderr=subprocess.PIPE
        ).decode()
        ud1 = str(uuid.uuid1()).replace('-','')
        self.s.cookies.set('_mb_tk', ud1)
        self.s.cookies.set('_sl', '1', domain='twitter.com')
        headers = self.headers.copy()
        headers.update({
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://twitter.com',
            'Referer': 'https://twitter.com/',
            'Cache-Control': 'max-age=0'
        })
        data = {
            'redirect_after_login': '/',
            'remember_me': 1,
            'authenticity_token': ud1,
            'wfa': 1,
            'ui_metrics': result,
            'session[username_or_email]': self.uname,
            'session[password]': self.__pwd
        }
        r = self.s.post(url=self.urls['login'], headers=headers, data=data, timeout=9)
        if r.status_code != 200:
            raise Exception('登录失败：', r.text)

    def DL(self, dic, ref):
        """
        下载推文附带的媒体
        :param dic: ‘extended_entities’的值
        :param ref: Referer
        :return: 保存的文件名或视频地址
        """
        headers = self.headers.copy()
        headers['Origin'] = 'https://twitter.com'
        headers['Referer'] = ref
        media_urls = []
        results = []
        for key in dic:
            for j in dic[key]:
                if j['type'] == 'video':
                    bitrate, vurl = 0, ''
                    for obj in j['video_info']['variants']:
                        if obj.__contains__('bitrate') and obj['bitrate']>bitrate:
                            bitrate = obj['bitrate']
                            vurl = obj['url']
                    media_urls.append(vurl)
                else:
                    media_urls.append(j['media_url'])
        for url in media_urls:
            url = url.split('?')[0]
            headers['Host'] = parse.urlparse(url).hostname
            r = self.s.get(url, headers=headers, timeout=36)
            if r.status_code != 200:
                raise Exception('下载资源失败', url)
            file_name = url.split('/')[-1]
            with open('.\\media\\'+file_name, 'wb') as mf:
                mf.write(r.content)
            results.append(file_name)
        return results

    @staticmethod
    def toUTC8(s):
        """
        将零时区转换为东八区
        :param s: 时间字符串
        :return s8: 东八区时间字符串
        """
        s = s.replace('+0000 ', '')
        tmp = time.mktime(time.strptime(s, '%a %b %d %H:%M:%S %Y'))+28800
        s8 = time.strftime('%m-%d %H:%M:%S', time.localtime(tmp))
        return s8
        
    def fetch_content(self, dic, key, ref):
        """
        推特文本处理
        :param dic:
        :param key:
        :param ref:
        :return:
        """
        users = dic['users']
        tweets = dic['tweets']
        media = None
        text = users[tweets[key]['user_id_str']]['name']+'\n'+self.toUTC8(tweets[key]['created_at'])+'\n'
        if tweets[key].__contains__('quoted_status_id_str'):
            q_key = tweets[key]['quoted_status_id_str']
            #过滤所有单纯转推
            #if 'RT @' == tweets[key]['full_text'][:4]:
            #    return {'text': '','media':None}
            text = text+tweets[key]['full_text'].replace('&gt;','>').replace('&lt;','<')+'\n\n转推了：\n\n'+users[tweets[q_key]['user_id_str']]['name']+'\n'+self.toUTC8(
                tweets[q_key]['created_at'])+'\n'+tweets[q_key]['full_text'].replace('&gt;','>').replace('&lt;','<')
            media = []
            if tweets[key].__contains__('extended_entities'):
                media = self.DL(tweets[key]['extended_entities'], ref)
            if tweets[q_key].__contains__('extended_entities'):
                media = media+self.DL(tweets[q_key]['extended_entities'], ref)
        elif tweets[key].__contains__('retweeted_status_id_str'):
            text = ''
        else:
            text = text+tweets[key]['full_text'].replace('&gt;','>').replace('&lt;','<')
            if tweets[key].__contains__('extended_entities'):
                media = self.DL(tweets[key]['extended_entities'], ref)
        return {'text': text,'media': media}

    def queryf(self, _name, mode=1):
        """
        查询指定用户followers数量
        :param _name: 查询对象姓名，汉字请使用标准简体中文
        :param mode: 模式，1为获取fo数并记录（默认），0为获取rest_id，并返回usr用于后续操作
        :return:
        """
        if not _name:
            raise Exception('所查询用户名为空')
        self.cursor.execute(f'select usrid from followers where name="{_name}"')
        usr = self.cursor.fetchone()[0]
        url = self.urls['ql']+self.queryid+\
              '/UserByScreenName?variables=%7B%22screen_name%22%3A%22{}%22%2C%22withHighlightedLabel%22%3Atrue%7D'.format(usr)
        ref = self.urls['main']+usr
        headers = self.headers.copy()
        headers.update({
            'Host': 'api.twitter.com',
            'Origin': 'https://twitter.com',
            'Referer': ref
        })
        headers.update({
            'authorization': 'Bearer '+self.authorization,
            'x-twitter-client-language': 'zh-cn',
            'x-csrf-token': self.s.cookies.get('ct0'),
            #'x-guest-token': self.s.cookies.get('gt'),
            'x-twitter-active-user': 'yes',
            'content-type': 'application/json'
        })
        try:
            r = self.s.get(url, headers=headers, timeout=18)
        except ProxyError:
            raise
        except Exception as e:
            logging.warning(repr(e))
            time.sleep(1)
            r = self.s.get(url, headers=headers, timeout=18)
        if '353' in r.text and 'csrf cookie' in r.text:
            headers['x-csrf-token'] = self.s.cookies.get('ct0')
            time.sleep(1)
            r = self.s.get(url, headers=headers, timeout=18)
        if r.status_code == 200:
            usr_data = r.json()['data']['user']
            if mode:
                flcount = usr_data['legacy']['followers_count']
                self.cursor.execute(f'select number from followers where name="{_name}"')
                floriginal = 0 if self.cursor.fetchone()[0] is None else self.cursor.fetchone()[0]
                increment = flcount-floriginal
                msg = '{0:{1}<6}{2:^9}{3:>6}'.format(_name, chr(12288), flcount, '+'+str(increment) if increment>=0 else increment)
                print(msg)
                self.msg = self.msg+msg+'\n\n'
                self.cursor.execute(f'update followers set number={flcount},time=current_timestamp() where name="{_name}"')
                # self.conn.commit()
            else:
                self.nid = usr_data['rest_id']
                return usr
        else:
            raise Exception(r.text)

    def queryt(self, _uname):
        """
        查询指定用户的推文更新
        :param _uname: 查询对象姓名，汉字请使用标准简体中文
        :return: dict, keys:“text”(推文内容)
                            "media"(媒体文件名)
                            @see: gettwi.DL
        """
        usr = self.queryf(_uname, mode=0)
        url = 'https://api.twitter.com/2/timeline/profile/{}.json'.format(self.nid)
        headers = self.headers.copy()
        headers.update({
            'Host': 'api.twitter.com',
            'authorization': 'Bearer '+self.authorization,
            'x-csrf-token': self.s.cookies.get('ct0'),
            'x-twitter-active-user': 'yes',
            'Origin': 'https://twitter.com',
            'Referer': 'https://twitter.com/'+usr
        })
        params = self.params.copy()
        params['include_tweet_replies'] = 'true'
        params['userId'] = self.nid
        r = self.s.get(url, headers=headers, params=params, timeout=18)
        if r.json().__contains__('errors'):
            raise Exception(r.text)
        ret = r.json()['globalObjects']
        users = ret['users']
        tweets = ret['tweets']
        latest = max(list(tweets.keys()))
        self.cursor.execute(f'select latest from followers where name="{_uname}"')
        latest0 = self.cursor.fetchone()[0]
        if latest0 is None:
            latest0 = '0'
        new_dics = []
        for key in tweets.keys():
            if int(key)>int(latest0) and tweets[key]['user_id_str'] == self.nid:
                new_dics.append(self.fetch_content(ret, key, headers['Referer']))
        if int(latest)>int(latest0):
            self.cursor.execute(f'update followers set latest="{latest}" where name="{_uname}"')
        return new_dics

    def update(self):
        """
        刷新推特时间线（英文作timeline。需要登录）
        :return: json对象，具体格式请查看twitter developer官方文档
        """
        if not self.islogin:
            logging.warning("update:未登录推特账号，无法刷新时间线")
            return
        headers = self.headers.copy()
        headers.update({
            'Host': 'api.twitter.com',
            'authorization': 'Bearer '+self.authorization,
            'x-csrf-token': self.s.cookies.get('ct0'),
            'x-twitter-client-language': self.s.cookies.get('lang'),
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-active-user': 'yes',
            'Origin': 'https://twitter.com',
            'Referer': 'https://twitter.com/home'
        })
        params = self.params.copy()
        params['earned'] = '1'
        r = self.s.get(url=self.urls['timeline'], headers=headers, params=params, timeout=18)
        return r.json()['globalObjects']


if __name__ == '__main__':
    #a = Gettwi()  # 不登录，这种情况无法使用update()
    #a = Gettwi(uname='+8616600000000', pwd='password')  # 填入推特账号和密码
    #ret = a.queryt('河濑诗')  # 查询指定用户的新推文
    t = Gettwi.toUTC8('Sun May 03 10:15:51 +0000 2020')
    print(t)
