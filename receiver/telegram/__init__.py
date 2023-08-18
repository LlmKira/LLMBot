# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:46
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

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

    def callback(self, data, ack):
        # 解析数据
        _task = TaskHeader.parse_obj(data)
        _llm = OpenaiMiddleware(task=_task)

        async def func():
            await _llm.func_message()

        print(_task)
        __sender__.bot.send_message(
            chat_id=_task.receiver.chat_id,
            text="received",
            reply_to_message_id=_task.receiver.message_id
        )
        ack()

    async def telegram(self):
        self.task.consuming_task(self.callback)
