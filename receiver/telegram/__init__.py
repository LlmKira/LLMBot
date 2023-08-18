# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

from aio_pika.abc import AbstractIncomingMessage
from telebot import TeleBot

from receiver.core import OpenaiMiddleware
from schema import TaskHeader, RawMessage
from setting.telegram import BotSetting
from task import Task

__receiver__ = "telegram"


class TelegramSender(object):
    def __init__(self):
        self.bot = TeleBot(token=BotSetting.token)
        if BotSetting.proxy_address:
            from telebot import apihelper
            apihelper.proxy = {'https': BotSetting.proxy_address}

    def send(self, chat_id, reply_to_message_id, message: List[RawMessage]):
        for item in message:
            self.bot.send_message(
                chat_id=chat_id,
                text=item.text,
                reply_to_message_id=reply_to_message_id
            )


__sender__ = TelegramSender()


class TelegramReceiver(object):
    """
    receive message from telegram
    """

    def __init__(self):
        self.task = Task(queue=__receiver__)

    async def on_message(self, message: AbstractIncomingMessage):
        # 解析数据
        _task = TaskHeader.parse_raw(message.body)
        print(" [x] Received %r" % _task)
        _llm = OpenaiMiddleware(task=_task)
        _message = await _llm.func_message()
        print(_message)
        __sender__.bot.send_message(
            chat_id=_task.receiver.chat_id,
            text=_message.content,
            reply_to_message_id=_task.receiver.message_id
        )
        print(" [x] Done")
        await message.ack()

    async def telegram(self):
        await self.task.consuming_task(self.on_message)
