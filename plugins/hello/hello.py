# encoding:utf-8
import random

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf
from .tencent_docs import get_docs_operator


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
            if rand_num < 0.01:  # 有100分之一的概率进入这个分支
                print("进入分支1: 获得VIP一个月")
                reply = Reply()
                reply.type = ReplyType.TEXT
                msg: ChatMessage = e_context["context"]["msg"]
                if e_context["context"]["isgroup"]:
                    reply.content = f"恭喜 {msg.actual_user_nickname} 拍出了一份奖品: 【一个月小助手VIP】, 请联系Tt获取"
                else:
                    reply.content = f"恭喜 {msg.from_user_nickname} 拍出了一份奖品: 【一个月小助手VIP】, 请联系Tt获取"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑，一般会覆写reply
                return
            elif rand_num < 0.2:  # 接下来有29%的概率（累计到30%）进入这个分支
                print("进入分支2: 随机Tips")
                e_context["context"].type = ContextType.TEXT
                e_context["context"].content = f"请你随机介绍一个简短的网球的小知识"
                e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
                return
            elif rand_num < 0.3:  # 接下来有29%的概率（累计到30%）进入这个分支
                print("进入分支2: 随机Tips")
                e_context["context"].type = ContextType.TEXT
                e_context["context"].content = f"请你随机介绍一个简短的提升网球水平的小知识"
                e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
                return
            else:  # 剩下的概率（70%）进入这个分支
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
