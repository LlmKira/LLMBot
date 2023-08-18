# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import hashlib
from io import BytesIO
from typing import Union, List, Any, Literal

from pydantic import Field, BaseModel
from telebot import types

from cache.redis import cache


def generate_md5_short_id(data):
    # 检查输入数据是否是一个文件
    is_file = False
    if isinstance(data, str):
        is_file = True
    if isinstance(data, BytesIO):
        data = data.getvalue()
    # 计算 MD5 哈希值
    md5_hash = hashlib.md5()
    if is_file:
        with open(data, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
    else:
        md5_hash.update(data)
    # 获取哈希值的 16 进制表示
    hex_digest = md5_hash.hexdigest()
    # 生成唯一的短ID
    short_id = hex_digest[:8]
    return short_id


class File(BaseModel):
    file_id: str = Field(None, description="文件ID")
    file_name: str = Field(None, description="文件名")
    file_url: str = Field(None, description="文件URL")


class RawMessage(BaseModel):
    user_id: int = Field(None, description="用户ID")
    chat_id: int = Field(None, description="群组ID")
    text: str = Field(None, description="文本")
    file: List[File] = Field([], description="文件")
    created_at: int = Field(None, description="创建时间")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @staticmethod
    async def download_file(file_id):
        return await cache.read_data(file_id)

    @staticmethod
    async def upload_file(name, data):
        _key = str(generate_md5_short_id(data))
        await cache.set_data(key=_key, value=data, timeout=60 * 60 * 24 * 7)
        return File(file_id=_key, file_name=name)

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
    def from_telegram(cls, message: Union[types.Message],
                      task_meta: Meta,
                      file: List[File] = None,
                      reply: bool = True,
                      hide_file_info: bool = False
                      ):
        """
        从telegram消息中构建任务
        """
        _file_name = []
        if file is None:
            file = []
        else:
            for _file in file:
                _file_name.append(f"![{_file.file_name}]")
        if isinstance(message, types.Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text if message.text else message.caption
            created_at = message.date
        else:
            raise ValueError(f"Unknown message type {type(message)}")
        if not hide_file_info:
            text += "\n" + "\n".join(_file_name)
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
                file=file,
                created_at=created_at
            )]
        )

    @classmethod
    def from_function(cls, parent_call: Any, task_meta: Meta, receiver: Location, message: List[RawMessage] = None):
        """
        从 Openai LLM Task中构建任务
        'function_call': {'name': 'set_alarm_reminder', 'arguments': '{\n  "delay": "5",\n  "content": "该吃饭了"\n}'}}
        """
        task_meta.parent_call = parent_call
        return cls(
            task_meta=task_meta,
            receiver=receiver,
            message=message
        )
