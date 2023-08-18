# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Union, List

from pydantic import Field, BaseModel
from telebot import types


class RawMessage(BaseModel):
    user_id: int = Field(None, description="用户ID")
    chat_id: int = Field(None, description="群组ID")
    text: str = Field(None, description="文本")
    created_at: int = Field(None, description="创建时间")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @classmethod
    def from_telegram(cls, message: Union[types.Message, types.CallbackQuery]):
        if isinstance(message, types.Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text
            created_at = message.date
        elif isinstance(message, types.CallbackQuery):
            user_id = message.from_user.id
            chat_id = message.message.chat.id
            text = message.data
            created_at = message.message.date
        else:
            raise ValueError(f"Unknown message type {type(message)}")
        return cls(
            user_id=user_id,
            text=text,
            chat_id=chat_id,
            created_at=created_at
        )


class TaskHeader(BaseModel):
    class Meta(BaseModel):
        function_enable: bool = Field(False, description="功能开关")

    class Location(BaseModel):
        platform: str = Field(None, description="平台")
        chat_id: Union[int, str] = Field(None, description="群组ID")
        user_id: Union[int, str] = Field(None, description="用户ID")
        message_id: Union[int, str] = Field(None, description="消息ID")

    task_meta: Meta = Field(None, description="任务元数据")
    receiver: Location = Field(None, description="接收人")
    message: List[RawMessage] = Field(None, description="消息内容")

    @classmethod
    def from_telegram(cls, message: Union[types.Message], task_meta: Meta, reply: bool = True):
        """
        从telegram消息中构建任务
        """
        if isinstance(message, types.Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text
            created_at = message.date
        else:
            raise ValueError(f"Unknown message type {type(message)}")
        return cls(
            task_meta=task_meta,
            receiver=cls.Location(
                platform="telegram",
                chat_id=chat_id,
                user_id=chat_id,
                message_id=message.message_id if reply else None
            ),
            message=[RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                text=text,
                created_at=message.date
            )]
        )
