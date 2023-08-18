# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 上午9:37
# @Author  : sudoskys
# @File    : core.py
# @Software: PyCharm
from typing import List

from loguru import logger

from schema import TaskHeader, RawMessage
from sdk.endpoint import openai
from sdk.endpoint.openai import Message
from sdk.endpoint.openai.action import Scraper
from sdk.func_call import TOOL_MANAGER
from sdk.memory.redis import RedisChatMessageHistory


class OpenaiMiddleware(object):
    """
    Openai中间件，用于处理消息转换和调用工具
    任务数据>转换器+函数填充>提取历史>放进刮削器>任务数据+刮削结果请求>获取Openai返回>进行声明通知/返回消息
    """

    def __init__(self, task: TaskHeader):
        self.driver = openai.Openai.Driver()
        self.scraper = Scraper()  # 刮削器
        self.functions = []
        self.task = task
        self.message_history = RedisChatMessageHistory(session_id=str(task.receiver.user_id))
        # 先拉取记录再转换
        self.create_message()

    def create_message(self):
        """
        转换消息
        """
        _history = []
        _buffer = []
        history_messages = self.message_history.messages
        for i, message in enumerate(history_messages):
            _history.append(message)
        # 实时消息
        raw_message = self.task.message
        raw_message: List[RawMessage]
        for i, message in enumerate(raw_message):
            _buffer.append(Message(role="user", content=message.text))
            # 创建函数系统
            if self.task.task_meta.function_enable:
                self.functions.extend(TOOL_MANAGER.run_all_check(message.text))
        # 刮削器合并消息
        _total = 0
        for i, _msg in enumerate(_history):
            _total += 1
            self.scraper.add_message(_msg, score=i, order=_total)
        for i, _msg in enumerate(_buffer):
            _total += 1
            self.scraper.add_message(_msg, score=i + 100, order=_total)
        # save to history
        for _msg in _buffer:
            self.message_history.add_message(message=_msg)

    async def func_message(self):
        """
        处理消息转换和调用工具
        """
        model_name = "gpt-3.5-turbo-0613"
        self.scraper.reduce_messages(limit=openai.Openai.get_token_limit(model=model_name))
        message = self.scraper.get_messages()
        # 消息缓存读取和转换
        endpoint = openai.Openai(config=self.driver, model=model_name, messages=message, functions=self.functions)
        # 调用Openai
        result = await endpoint.create()
        logger.info(f"openai result:{result}")
