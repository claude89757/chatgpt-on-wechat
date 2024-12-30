# encoding:utf-8

import os
import time
import json
import openai
from openai import AzureOpenAI
import datetime

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config

from bot.chatgpt.azure_agent import AzureOpenAIAgent


# OpenAI对话模型API (可用)
class ChatGPTBot(Bot):
    def __init__(self):
        # set the default api_key
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://chatgpt3.openai.azure.com/")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = "2024-05-01-preview"
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-4o-mini")

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply

            # # 标记AI视频分析任务
            # if query == "动作分析" or str(query).upper() == "AI视频" or query == "动作打分" or query == "分析动作":
            #     # 指定要写入的文件名
            #     file_name = "trigger_ai_video_time.txt"

            #     # 检查文件是否存在
            #     if os.path.exists(file_name):
            #         # 获取文件的最后修改时间
            #         last_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
            #         current_time = datetime.datetime.now()
            #         time_diff = current_time - last_modified_time

            #         # 如果文件的最后修改时间超过30分钟，则清空文件内容
            #         if time_diff > datetime.timedelta(minutes=30):
            #             with open(file_name, "w", encoding="utf-8") as file:
            #                 file.write("")
            #             print(f"文件 '{file_name}' 超过30分钟未更新，已清空内容。")
            #         else:
            #             # 读取文件内容
            #             with open(file_name, "r", encoding="utf-8") as file:
            #                 content = file.read()
            #                 # 检查是否包含 "RUNNING" 字符串
            #                 if "RUNNING" in content:
            #                     reply = Reply(ReplyType.TEXT, "其他任务执行中，请5~10分钟后重新触发Zacks")
            #                     return reply

            #     # 将当前时间和其他信息写入文件
            #     with open(file_name, "w", encoding="utf-8") as file:
            #         json_data = {
            #             "from_user_nickname": context.kwargs.get('msg').from_user_nickname,
            #             "to_user_nickname": context.kwargs.get('msg').to_user_nickname,
            #             "self_display_name": context.kwargs.get('msg').self_display_name,
            #             "status": "RUNNING",
            #             "timestamp": datetime.datetime.now().isoformat()
            #         }
            #         file.write(json.dumps(json_data))
            #     print(f"'{json_data}' 已写入到 '{file_name}' 文件中。")
            #     reply = Reply(ReplyType.TEXT, "正在触发AI视频分析任务...")
            #     return reply
            # else:
            #     pass

            # # 问题类型分类
            # logger.info(f"0. what kind of query for: {query}")
            # azure_agent = AzureOpenAIAgent("gpt-4o-mini")
            # response = azure_agent.agent_question_analysis(query)
            # logger.info(f"query type: {response}")
            # if "" in response:
            #     logger.info(f"1. query for tennis court agent: {query}")
            #     response = azure_agent.agent_tennis_court(query)
            #     logger.info(f"tennis court agent response: {response}")
            #     return Reply(ReplyType.TEXT, response)
            # else:
            # 其他
            logger.info(f"2. query for other chat: {query}")
            self.sessions.clear_all_session()
            session = self.sessions.session_query(query, session_id)
            logger.debug("[CHATGPT] session query={}".format(session.messages))

            reply_content = self.reply_text(session)
            logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            reply = Reply(ReplyType.ERROR, "Not supported.")
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param retry_count: retry count
        :return: {}
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=session.messages,
                temperature=0.7,
                top_p=1,
                # max_tokens=2024,
            )
            logger.info("[CHATGPT] response={}".format(response))
            logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0].message.content,
                                                                     response.usage.total_tokens))
            return {
                "total_tokens": response.usage.total_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "content": response.choices[0].message.content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.RateLimitError):
                logger.warn("[CHATGPT] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.Timeout):
                logger.warn("[CHATGPT] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.APIError):
                logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.APIConnectionError):
                logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.exception("[CHATGPT] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result


class AzureChatGPTBot(ChatGPTBot):
    def __init__(self):
        super().__init__()

    def create_img(self, query, retry_count=0, api_key=None):
        """
        生成图像的代码
        """
        raise NotImplementedError
