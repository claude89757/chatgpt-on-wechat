# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf


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
            e_context["context"].type = ContextType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            e_context["context"].content = f"请你随机介绍一个简短的网球的小知识"
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑
            return

        content = e_context["context"].content
        logger.debug("[Hello] on_handle_context. content: %s" % content)
        if content == "Hello":
            reply = Reply()
            reply.type = ReplyType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            if e_context["context"]["isgroup"]:
                reply.content = f"Hello, {msg.actual_user_nickname} from {msg.from_user_nickname}"
            else:
                reply.content = f"Hello, {msg.from_user_nickname}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        keywords = ["大沙河", "深云", "深圳湾", "香蜜", "莲花", "简上", "黄木岗", "华侨城", "福田中心",
                    "黄冈公园", "北站公园", "威新", "泰尼斯", "总裁", "郑洁", "梅林", "二村", "山花"]
        hit_keyword = False
        for keyword in keywords:
            if keyword in content:
                print(f"字符串包含{keyword}")
                hit_keyword = True
                break
            else:
                pass
        if ("订" in content or "定" in content) and (("场地" in content or "场" in content) or hit_keyword):
            e_context["context"].type = ContextType.TEXT
            court_msg = """序号	场地名称	价格	订场方式	场地类型	提前预定时间	场地联系电话	备注
1	大沙河	17:00前60/h,17:00后100/h	i深圳/小程序：南山文体通	室外场	7天	18922805664	无
2	深云文体	17:00前80/h,17:00后160/h	i深圳APP	室外场	1天	0755-88977900	无
3	深圳湾	未知	i深圳APP	室外场	1天	0755-86308856	电话预定仅支持当日
4	香蜜体育	17:00前50/h,17:00后90/h	i深圳APP/公众号：福田Sport	室外场	1天	0755-83771352	6号场地，当日7点后电话预定
5	莲花体育	17:00前50/h,17:00后80/h	i深圳APP/公众号：福田Sport	室外场	1天	0755-82770388	无
6	简上	15:00前200/h,15:00后300/h	i深圳APP	室内场	3天	未知	无
7	黄木岗	风雨场：17:00前130/h,17:00后170/h
室外场：17:00前50/h,17:00后90/h	i深圳APP/公众号：福田Sport	风雨场	1天	0755-82770188	无
8	华侨城	17:00前100/h,17:00后130/h	i深圳APP	室外场	2天	18565791161	无
9	福田中心	17:00前80/h,17:00后120/h	i深圳APP/公众号：福田Sport	室外场	7天	18923703457	无
10	黄冈公园	17:00前120/h,17:00后140/h	i深圳APP/公众号：福田Sport	室外场	未知	未知	无
11	北站公园	17:00前120/h,17:00后140/h	i深圳APP/公众号：福田Sport	室外场	未知	未知	无
12	金地威新	16:00前115/h,16:00后130/h	小程序：ING在运动	室外场	2天	未知	一般场地当日释放，可在下午电话场地管理处，咨询是否当晚是否有空场
13	泰尼斯香蜜	17:00前150/h,17:00后220/h	小程序：泰尼斯体育	室外场	未知	未知	无
14	总裁俱乐部	未知	i深圳APP/公众号：尚酷网球	室外场	未知	未知	无
15	郑洁俱乐部	17:00前80/h,17:00后120/h	i深圳APP/公众号：郑洁网球俱乐部	室外场	未知	未知	无
16	梅林文体	17:00前65/h	i深圳APP/公众号：昊创文体	室外场	未知	未知	无
17	莲花二村	17:00前70/h,17:00后100/h	微信公众号：大生体育	室外场	未知	未知	无
18	深圳湾山花馆	17:00前100/h,17:00后150/h	微信公众号：山花体育	室外场	未知	未知	无"""
            new_context = f"{court_msg}\n请根据以上场地信息回答一下问题: {content}"
            e_context["context"].content = new_context
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑

        if content == "Hi":
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "Hi"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑，一般会覆写reply

        if content == "End":
            # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
            e_context["context"].type = ContextType.IMAGE_CREATE
            content = "The World"
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "输入Hello，我会回复你的名字\n输入End，我会回复你世界的图片\n"
        return help_text
