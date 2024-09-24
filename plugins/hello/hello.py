# encoding:utf-8
import random
import datetime
import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf
from lib.tencent_docs.tencent_docs import get_docs_operator


def load_last_sent_message():
    """从本地文件加载最后一次发送的消息"""
    try:
        with open("last_sent_message.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return None  # 如果文件不存在，返回None


def clear_last_sent_message():
    """清空保存的最后一次发送的消息文件"""
    with open("last_sent_message.txt", "w") as file:
        file.write("")  # 写入空字符串以清空文件内容


def get_realtime_tennis_court_msg(last_sent_msg: str):
    """
    查询最新发送的网球场的状态
    """
    try:
        place_name = last_sent_msg.split('】')[0].split('【')[-1]
        date = f"{datetime.datetime.now().year}-{last_sent_msg.split('(')[1].split(')')[0]}"
        msg_list = []
        error_msg_list = []
        for time_range_str in last_sent_msg.split()[1].split('|'):
            start_time = time_range_str.split('-')[0]
            end_time = time_range_str.split('-')[1]
            url = "https://1300108802-gl3lbnqt81-gz.scf.tencentcs.com"
            data = {
                'place_name': place_name,
                'date': date,
                'start_time': start_time,
                'end_time': end_time
            }
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers)
            print(response.text)
            if response.status_code == 200:
                res = response.json()
                if res.get('code') == 0:
                    court_msg = res['data']
                    if "已被预定" in court_msg:
                        clear_last_sent_message()
                    else:
                        pass
                    msg_list.append(court_msg)
                else:
                    error_msg_list.append("Ops, CPU烧了o(╥﹏╥)o")
            else:
                error_msg_list.append(f"错误代码: {response.status_code}")
        if msg_list:
            msg = "\n".join(msg_list)
        else:
            msg = "\n".join(error_msg_list)
        return msg
    except requests.RequestException as error:
        print(error)
        return "Ops, 出错了o(╥﹏╥)o"


@plugins.register(
    name="Hello",
    desire_priority=-1,
    hidden=True,
    desc="A simple plugin that says hello",
    version="0.1",
    author="lanvent",
)
class Hello(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Hello] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,
            ContextType.JOIN_GROUP,
            ContextType.PATPAT,
        ]:
            logger.error(f"????????????????????: {e_context['context'].type}")
            return

        if e_context["context"].type == ContextType.JOIN_GROUP:
            if "group_welcome_msg" in conf():
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = conf().get("group_welcome_msg", "")
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
                return
            e_context["context"].type = ContextType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            e_context["context"].content = f'请你随机使用一种风格说一句问候语来欢迎新用户"{msg.actual_user_nickname}"加入群聊。'
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
            return

        if e_context["context"].type == ContextType.PATPAT:
            # 生成一个0到1之间的随机浮点数
            rand_num = random.random()
            # 判断随机数
            if rand_num < 0.1:  # 接下来有10%的概率进入这个分支
                print("进入分支1: 随机Tips")
                e_context["context"].type = ContextType.TEXT
                e_context["context"].content = f"请你随机介绍一个简短的网球的小知识"
                e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
                return
            elif rand_num < 0.2:  # 接下来有10%的概率进入这个分支
                print("进入分支2: 随机Tips")
                e_context["context"].type = ContextType.TEXT
                e_context["context"].content = f"请你随机介绍一个简短的提升网球水平的小知识"
                e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
                return
            else:  # 剩下的概率进入这个分支
                # last_sent_msg = load_last_sent_message()
                # if last_sent_msg:
                #     print("进入分支4: 查询最新发送的场地的实时状态")
                #     court_msg = get_realtime_tennis_court_msg(last_sent_msg)  # 获取网球场实时状态
                #     reply = Reply()
                #     reply.type = ReplyType.TEXT
                #     reply.content = court_msg
                #     e_context["reply"] = reply
                #     e_context.action = EventAction.BREAK_PASS  # 事件结束，进入默认处理逻辑，一般会覆写reply
                #     return
                # else:
                print("进入分支3: 发送网球场动态")
                docs = get_docs_operator()
                court_msg = docs.get_today_court_msg()  # 获取当日网球场状态
                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = court_msg
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS  # 事件结束，进入默认处理逻辑，一般会覆写reply
                return

        content = e_context["context"].content
        logger.debug("[Hello] on_handle_context. content: %s" % content)
        if str(content).lower() == "hello" or str(content).lower() == "hi":
            reply = Reply()
            reply.type = ReplyType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            if e_context["context"]["isgroup"]:
                reply.content = f"Hello, {msg.actual_user_nickname} from {msg.from_user_nickname}"
            else:
                reply.content = f"Hello, {msg.from_user_nickname}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        # if content == "End":
        #     # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
        #     e_context["context"].type = ContextType.IMAGE_CREATE
        #     content = "The World"
        #     e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "输入Hello，我会回复你的名字\n输入End，我会回复你世界的图片\n"
        return help_text
