# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from typing import Union, List, Any, Literal

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
        class Callback(BaseModel):
            role: Literal["user", "system", "function", "assistant"] = Field("user", description="角色")
            name: str = Field(None, description="功能名称", regex=r"^[a-zA-Z0-9_]+$")

        no_future_action: bool = Field(False, description="不进行后续操作")
        function_enable: bool = Field(False, description="功能开关")
        parent_call: Any = Field(None, description="父消息")
        callback: Callback = Field(Callback(), description="函数回调信息")

        class Config:
            arbitrary_types_allowed = True

    class Location(BaseModel):
        platform: str = Field(None, description="平台")
        chat_id: Union[int, str] = Field(None, description="群组ID")
        user_id: Union[int, str] = Field(None, description="用户ID")
        message_id: Union[int, str] = Field(None, description="消息ID")

    task_meta: Meta = Field(Meta(), description="任务元数据")
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
                created_at=created_at
            )]
        )

    @classmethod
    def from_function(cls, parent_call: Any, task_meta: Meta, receiver: Location):
        """
        从 Openai LLM Task中构建任务
        'function_call': {'name': 'set_alarm_reminder', 'arguments': '{\n  "delay": "5",\n  "content": "该吃饭了"\n}'}}
        """
        task_meta.parent_call = parent_call
        return cls(
            task_meta=task_meta,
            receiver=receiver,
            message=[]
        )
