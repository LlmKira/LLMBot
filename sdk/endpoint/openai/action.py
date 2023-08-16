# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:05
# @Author  : sudoskys
# @File    : action.py
# @Software: PyCharm
from typing import List

import tiktoken
from pydantic import BaseModel

from .schema import Message


class Scraper(BaseModel):
    """
    刮削器
    始终按照顺序排列，削除得分低的条目
    Scraper is a class that sorts a list of messages by their score.
    """

    class Sorter(BaseModel):
        message: Message
        # 得分
        score: float
        # 顺序
        order: int

    # 消息列表
    messages: list[Sorter] = []
    # 最大消息数
    max_messages: int = 10

    # 方法：添加消息
    def add_message(self, message: Message, score: float, order: int):
        self.messages.append(self.Sorter(message=message, score=score, order=order))
        self.messages.sort(key=lambda x: x.score, reverse=True)
        if len(self.messages) > self.max_messages:
            self.messages.pop()

    # 方法：获取消息
    def get_messages(self) -> list[Message]:
        return [message.message for message in self.messages]

    # 方法：获取消息数
    def get_num_messages(self) -> int:
        return len(self.messages)


class Tokenizer(object):
    __encode_cache = {}

    def clear_cache(self):
        self.__encode_cache = {}

    def num_tokens_from_messages(self, messages: List[Message], model="gpt-3.5-turbo-0613") -> int:
        """Return the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.dict().items():
                # 缓存获取 cache，减少重复 encode 次数
                if value in self.__encode_cache:
                    _tokens = self.__encode_cache[value]
                else:
                    _tokens = len(encoding.encode(value))
                    self.__encode_cache[value] = _tokens
                num_tokens += _tokens
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


TokenizerObj = Tokenizer()
