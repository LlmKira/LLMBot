# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Union

from pydantic import Field, BaseModel
from telebot import types


class Message(BaseModel):
    user_id: int = Field(None, description="用户ID")
    chat_id: int = Field(None, description="群组ID")
    text: str = Field(None, description="文本")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @classmethod
    def from_telegram(cls, message: Union[types.Message, types.CallbackQuery]):
        if isinstance(message, types.Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text
        elif isinstance(message, types.CallbackQuery):
            user_id = message.from_user.id
            chat_id = message.message.chat.id
            text = message.data
        else:
            raise ValueError(f"Unknown message type {type(message)}")
        return cls(
            user_id=user_id,
            text=text,
            chat_id=chat_id
        )
