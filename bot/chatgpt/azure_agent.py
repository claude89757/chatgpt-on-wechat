import os
import time
import openai
from openai import AzureOpenAI


class AzureOpenAIAgent:
    def __init__(self, model: str):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://chatgpt3.openai.azure.com/")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = "2024-05-01-preview"
        self.model = model
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.assistant = None

    def create_assistant(self, model, instructions, tools, tool_resources, temperature):
        self.assistant = self.client.beta.assistants.create(
            model=model,
            instructions=instructions,
            tools=tools,
            tool_resources=tool_resources,
            temperature=temperature,
        )

    def ask_question(self, question):
        if not self.assistant:
            raise Exception("Assistant not created. Please create an assistant first.")

        try:
            # 创建一个线程
            thread = self.client.beta.threads.create()

            # 添加用户问题到线程
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=question
            )

            # 运行线程
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant.id,
            )

            # 循环直到运行完成或失败
            start_time = time.time()
            while run.status in ['queued', 'in_progress', 'cancelling', 'incomplete']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                # 检查是否超时
                elapsed_time = time.time() - start_time
                if elapsed_time > 60:
                    raise TimeoutError(f"Operation timed out after {60} seconds")

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                for message in messages:
                    if message.role == 'assistant':
                        return message.content[0].text.value
            else:
                raise Exception(f"run.status: {run.status}")
        except Exception as error:
            return f"Ops, 出错了: {error}"

    def agent_tennis_court(self, question):
        self.create_assistant(
            model=self.model,
            instructions="你是网球场预定小助手，请根据文档，回答用户的问题。"
                         "风格要求：回答简单明了，不要超过140个字"
                         "其他要求：不捏造事实，如文档中无相关信息，则回答不知道，并欢迎协助录入更多场地信息。",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": ["vs_s8zsOws6u0NNOwkJV6gszCXA"]}},
            temperature=0.1,
        )
        return self.ask_question(question)

    def agent_question_analysis(self, question):
        self.create_assistant(
            model=self.model,
            instructions="""你是一个问题分类助手，参考【提示知识】，将问题分为两类：场地相关问题 和 其他问题
            【提示知识】
            1. 场地相关的关键字：大沙河、深圳湾、香蜜、金地、威新、网羽、黄木岗、简上、深云、莲花、华侨城、北站、泰尼斯、总裁、梅林、山花、
            场、场地、预约、预定、订
            2. 与场地相关的关键字关联，均为场地相关问题
            """,
            tools=[],
            tool_resources={},
            temperature=0.2,
        )
        return self.ask_question(question)

    def agent_other(self, question, instructions: str = ""):
        self.create_assistant(
            model=self.model,
            instructions=instructions,
            tools=[],
            tool_resources={},
            temperature=0.96,
        )
        return self.ask_question(question)


# 使用示例
if __name__ == "__main__":
    print(openai.RateLimitError)
    try:
        agent = AzureOpenAIAgent("gpt-4o-mini")
        response = agent.agent_question_analysis("大沙河在哪？")
        print(response)
    except openai.RateLimitError:
        print(123)
