# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:05
# @Author  : sudoskys
# @File    : action.py
# @Software: PyCharm
import hashlib
import json
from typing import List

import tiktoken
from pydantic import BaseModel

from sdk.schema import Message


# 生成MD5
def generate_md5(string):
    hl = hashlib.md5()
    hl.update(string.encode(encoding='utf-8'))
    return str(hl.hexdigest())


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
                if isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=True)
                _uid = generate_md5(str(value))
                # 缓存获取 cache，减少重复 encode 次数
                if _uid in self.__encode_cache:
                    _tokens = self.__encode_cache[_uid]
                else:
                    _tokens = len(encoding.encode(value))
                    self.__encode_cache[_uid] = _tokens
                num_tokens += _tokens
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


TokenizerObj = Tokenizer()


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
    max_messages: int = 100

    # 方法：添加消息
    def add_message(self, message: Message, score: float, order: int):
        if hasattr(message, "function_call"):
            return None
        self.messages.append(self.Sorter(message=message, score=score, order=order))
        # 按照顺序排序
        self.messages.sort(key=lambda x: x.order)
        if len(self.messages) > self.max_messages:
            self.messages.pop()

    # 方法：获取消息
    def get_messages(self) -> list[Message]:
        # 按照顺序排序
        self.messages.sort(key=lambda x: x.order)
        _message = [message.message for message in self.messages]
        # 去重
        # [*dict.fromkeys(_message)]
        # -> unhashable type: 'Message'
        print(_message)
        return _message

    # 方法：获取消息数
    def get_num_messages(self) -> int:
        return len(self.messages)

    # 方法：清除消息到负载
    def reduce_messages(self, limit: int = 2048):
        if TokenizerObj.num_tokens_from_messages(self.get_messages()) > limit:
            # 从最低得分开始删除
            self.messages.sort(key=lambda x: x.score)
            while TokenizerObj.num_tokens_from_messages(self.get_messages()) > limit:
                if len(self.messages) > 1:
                    self.messages.pop(0)
                else:
                    self.messages[0].message.content = self.messages[0].message.content[:limit]
        # 按照顺序排序
        self.messages.sort(key=lambda x: x.order)
