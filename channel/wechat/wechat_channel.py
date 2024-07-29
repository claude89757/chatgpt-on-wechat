# encoding:utf-8

"""
wechat channel
"""

import io
import json
import os
import threading
import time
import fcntl
import datetime

import requests

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.wechat.wechat_message import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from common.time_check import time_checker
from config import conf, get_appdata_dir
from lib import itchat
from lib.itchat.content import *
from lib.tencent_docs.tencent_docs import get_docs_operator


@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE, ATTACHMENT, SHARING])
def handler_single_msg(msg):
    try:
        cmsg = WechatMessage(msg, False)
    except NotImplementedError as e:
        logger.debug("[WX]single message {} skipped: {}".format(msg["MsgId"], e))
        return None
    WechatChannel().handle_single(cmsg)
    return None


@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE, ATTACHMENT, SHARING], isGroupChat=True)
def handler_group_msg(msg):
    try:
        cmsg = WechatMessage(msg, True)
    except NotImplementedError as e:
        logger.debug("[WX]group message {} skipped: {}".format(msg["MsgId"], e))
        return None
    WechatChannel().handle_group(cmsg)
    return None


def _check(func):
    def wrapper(self, cmsg: ChatMessage):
        msgId = cmsg.msg_id
        if msgId in self.receivedMsgs:
            logger.info("Wechat message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = True
        create_time = cmsg.create_time  # 消息时间戳
        if conf().get("hot_reload") == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message {} skipped".format(msgId))
            return
        if cmsg.my_msg and not cmsg.is_group:
            logger.debug("[WX]my message {} skipped".format(msgId))
            return
        return func(self, cmsg)

    return wrapper


# 可用的二维码生成接口
# https://api.qrserver.com/v1/create-qr-code/?size=400×400&data=https://www.abc.com
# https://api.isoyu.com/qr/?m=1&e=L&p=20&url=https://www.abc.com
def qrCallback(uuid, status, qrcode):
    # logger.debug("qrCallback: {} {}".format(uuid,status))
    if status == "0":
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(qrcode))
            _thread = threading.Thread(target=img.show, args=("QRCode",))
            _thread.setDaemon(True)
            _thread.start()
        except Exception as e:
            pass

        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr_api1 = "https://api.isoyu.com/qr/?m=1&e=L&p=20&url={}".format(url)
        qr_api2 = "https://api.qrserver.com/v1/create-qr-code/?size=400×400&data={}".format(url)
        qr_api3 = "https://api.pwmqr.com/qrcode/create/?url={}".format(url)
        qr_api4 = "https://my.tv.sohu.com/user/a/wvideo/getQRCode.do?text={}".format(url)
        print("You can also scan QRCode in any website below:")
        print(qr_api3)
        print(qr_api4)
        print(qr_api2)
        print(qr_api1)

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)


def get_bing_news_msg(query: str) -> list:
    """
    get data from bing
    This sample makes a call to the Bing Web Search API with a query and returns relevant web search.
    Documentation: https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
    """
    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    bing_subscription_key = os.environ.get("BING_KEY")
    if not bing_subscription_key:
        raise Exception("no BING_KEY!!!")

    endpoint = "https://api.bing.microsoft.com/v7.0/search"

    # Construct a request
    mkt = 'zh-HK'
    params = {'q': query, 'mkt': mkt, 'answerCount': 5, 'promote': 'News', 'freshness': 'Day'}
    headers = {'Ocp-Apim-Subscription-Key': bing_subscription_key}

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=60)
        response.raise_for_status()

        print(response.headers)
        # pprint(response.json())
        data = response.json()

        return data['news']['value']
    except Exception as error:
        return [{"name": f"Ops, 我崩溃了: {error}", "url": "？"}]


def save_message_to_file(message):
    """将消息保存到本地文件中"""
    with open("last_sent_message.txt", "w") as file:
        file.write(message)


def load_last_sent_message():
    """从本地文件加载最后一次发送的消息"""
    try:
        with open("last_sent_message.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return None  # 如果文件不存在，返回None


def create_loop_task():
    """
    创建一个循环任务，用于定时发送消息到部分群聊
    """
    # Create a timed loop task that check a file's content every 60 seconds
    print(f"creating a loop task...")
    def timed_loop_task():
        # 开始循环
        is_send_msg_list = []
        sent_6am = False
        sent_12am = False
        sent_18am = False
        old_news_list = []
        while True:
            print("start loop task...")
            # 查询网球场状态
            now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            chat_rooms = itchat.get_chatrooms(update=True, contactOnly=True)
            print(f"chat_rooms:---------------------------------------")
            for chat_room in chat_rooms:
                print(chat_room)
            print(f"chat_rooms:---------------------------------------")
            try:
                docs = get_docs_operator()
                for chat_room in chat_rooms:
                    up_for_send_msg = docs.get_up_for_send_msg_list()  # 获取当日网球场状态
                    for msg in up_for_send_msg:
                        if msg in is_send_msg_list:
                            pass
                        else:
                            if not is_send_msg_list:
                                # 首次启动
                                pass
                                is_send_msg_list.append(msg)
                            else:
                                # 非首次启动
                                print(f"{now} sending {msg}")
                                itchat.send_msg(msg=msg, toUserName=chat_room['UserName'])
                                is_send_msg_list.append(msg)
                                save_message_to_file(msg)  # 保存消息到文件
            except Exception as error:
                print(f"looping error: {error}")

            # 查询每日新闻
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            today = datetime.datetime.now()
            date_str = today.strftime("%m月%d日")
            weekday_str = today.strftime("%A")
            weekday_dict = {'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
                            'Thursday': '星期四', 'Friday': '星期五', 'Saturday': '星期六', 'Sunday': '星期日'}
            weekday_cn = weekday_dict[weekday_str]
            # 检查是否是早上8点或18点，并且还未发送消息
            if (current_hour == 6 and not sent_6am) or (current_hour == 12 and not sent_12am) \
                    or (current_hour == 18 and not sent_18am):
                # 查询新闻
                news_list = get_bing_news_msg(query='网球')
                # 组合消息
                msg_list = []
                for news_data in news_list:
                    print(news_data)
                    if news_data['name'] in old_news_list:
                        pass
                    else:
                        msg_list.append(f"{news_data['name']}")
                        msg_list.append(f"{news_data.get('url')}\n")
                        old_news_list.append(news_data['name'])
                if current_hour == 6:
                    first_line = f"【每日🎾】 早上好 {weekday_cn} {date_str} \n------"
                    sent_6am = True
                elif current_hour == 12:
                    first_line = f"【每日🎾】 中午好 {weekday_cn} {date_str} \n------"
                    sent_12am = True
                else:
                    first_line = f"【每日🎾】 下午好 {weekday_cn} {date_str} \n------"
                    sent_18am = True
                if msg_list:
                    msg_list.insert(0, first_line)
                else:
                    msg_list.append(first_line)
                    msg_list.append("好像没什么新闻o(╥﹏╥)o")
                msg = '\n'.join(msg_list)
                for chat_room in chat_rooms:
                    itchat.send_msg(msg=msg, toUserName=chat_room['UserName'])

            # 每天重置发送状态
            if current_hour == 0 and current_minute <= 1:
                is_send_msg_list.clear()
                old_news_list.clear()
                sent_6am = False
                sent_12am = False
                sent_18am = False

            # 循环等待时间
            print("sleeping for 120s")
            time.sleep(120)

    # Start the thread
    thread = threading.Thread(target=timed_loop_task, daemon=True)
    thread.start()


@singleton
class WechatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.receivedMsgs = ExpiredDict(60 * 60)

    def startup(self):
        itchat.instance.receivingRetryCount = 600  # 修改断线超时时间
        # login by scan QRCode
        hotReload = conf().get("hot_reload", False)
        status_path = os.path.join(get_appdata_dir(), "itchat.pkl")
        itchat.auto_login(
            enableCmdQR=2,
            hotReload=hotReload,
            statusStorageDir=status_path,
            qrCallback=qrCallback,
        )
        self.user_id = itchat.instance.storageClass.userName
        self.name = itchat.instance.storageClass.nickName
        logger.info("Wechat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))

        # create_loop_task
        create_loop_task()

        # start message listener
        itchat.run()

    # handle_* 系列函数处理收到的消息后构造Context，然后传入produce函数中处理Context和发送回复
    # Context包含了消息的所有信息，包括以下属性
    #   type 消息类型, 包括TEXT、VOICE、IMAGE_CREATE
    #   content 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   kwargs 附加参数字典，包含以下的key：
    #        session_id: 会话id
    #        isgroup: 是否是群聊
    #        receiver: 需要回复的对象
    #        msg: ChatMessage消息对象
    #        origin_ctype: 原始消息类型，语音转文字后，私聊时如果匹配前缀失败，会根据初始消息是否是语音来放宽触发规则
    #        desire_rtype: 希望回复类型，默认是文本回复，设置为ReplyType.VOICE是语音回复

    @time_checker
    @_check
    def handle_single(self, cmsg: ChatMessage):
        # filter system message
        if cmsg.other_user_id in ["weixin"]:
            return
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return
            logger.debug("[WX]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[WX]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[WX]receive text msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        else:
            logger.debug("[WX]receive msg: {}, cmsg={}".format(cmsg.content, cmsg))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @time_checker
    @_check
    def handle_group(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("group_speech_recognition") != True:
                return
            logger.debug("[WX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT, ContextType.ACCEPT_FRIEND]:
            logger.debug("[WX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            # logger.debug("[WX]receive group msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
            pass
        elif cmsg.ctype == ContextType.FILE:
            logger.debug(f"[WX]receive attachment msg, file_name={cmsg.content}")
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type == ReplyType.TEXT:
            itchat.send(reply.content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            itchat.send(reply.content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.VOICE:
            itchat.send_file(reply.content, toUserName=receiver)
            logger.info("[WX] sendFile={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            logger.debug(f"[WX] start download image, img_url={img_url}")
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            size = 0
            for block in pic_res.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            logger.info(f"[WX] download image success, size={size}, img_url={img_url}")
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage, receiver={}".format(receiver))
        elif reply.type == ReplyType.FILE:  # 新增文件回复类型
            file_storage = reply.content
            itchat.send_file(file_storage, toUserName=receiver)
            logger.info("[WX] sendFile, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO:  # 新增视频回复类型
            video_storage = reply.content
            itchat.send_video(video_storage, toUserName=receiver)
            logger.info("[WX] sendFile, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO_URL:  # 新增视频URL回复类型
            video_url = reply.content
            logger.debug(f"[WX] start download video, video_url={video_url}")
            video_res = requests.get(video_url, stream=True)
            video_storage = io.BytesIO()
            size = 0
            for block in video_res.iter_content(1024):
                size += len(block)
                video_storage.write(block)
            logger.info(f"[WX] download video success, size={size}, video_url={video_url}")
            video_storage.seek(0)
            itchat.send_video(video_storage, toUserName=receiver)
            logger.info("[WX] sendVideo url={}, receiver={}".format(video_url, receiver))
