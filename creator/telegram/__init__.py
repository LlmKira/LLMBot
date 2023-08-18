# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:19
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm

from loguru import logger
from telebot import formatting
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.formatting import escape_markdown

from schema import TaskHeader
from setting.telegram import BotSetting
from task import Task

StepCache = StateMemoryStorage()
__sender__ = "telegram"
TelegramTask = Task(queue=__sender__)


class TelegramBotRunner(object):
    def __init__(self):
        self.bot = AsyncTeleBot(BotSetting.token, state_storage=StepCache)
        self.proxy = BotSetting.proxy_address

    def telegram(self):
        logger.success("Telegram Bot Start")
        bot = self.bot
        if self.proxy:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy
            logger.info("Proxy tunnels are being used!")

        async def is_admin(message: types.Message):
            _got = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return _got.status in ['administrator', 'creator']

        async def create_task(message: types.Message, funtion_enabled: bool = False):
            return TelegramTask.send_task(
                task=TaskHeader.from_telegram(
                    message,
                    task_meta=TaskHeader.Meta(function_enabled=funtion_enabled)
                )
            )

        @bot.message_handler(commands='bind', chat_types=['private'])
        async def listen_bind_command(message: types.Message):
            # TODO: 自动订阅系统
            return logger.warning("订阅系统")

        @bot.message_handler(content_types=['text'], chat_types=['private'])
        async def handle_private_msg(message: types.Message):
            """
            自动响应私聊消息
            """
            return await create_task(message, funtion_enabled=False)

        @bot.message_handler(commands='task', chat_types=['private', 'supergroup', 'group'])
        async def listen_task_command(message: types.Message):
            """/task - 任务
            """
            return await create_task(message, funtion_enabled=True)

        @bot.message_handler(content_types=['text'], chat_types=['supergroup', 'group'])
        async def handle_group_msg(message: types.Message):
            if not message.text:
                return None
            if message.text.startswith("/chat"):
                return await create_task(message, funtion_enabled=False)
            if f"@{BotSetting.bot_username} " in message.text or message.text.endswith(f" @{BotSetting.bot_username}"):
                return await create_task(message, funtion_enabled=False)

        @bot.message_handler(commands='tool', chat_types=['private', 'supergroup', 'group'])
        async def listen_tool_command(message: types.Message):
            """/tool - 工具列表
            """
            # TODO: 生成工具列表，完善插件系统
            return logger.warning("工具列表")

        @bot.message_handler(commands='help', chat_types=['private', 'supergroup', 'group'])
        async def listen_help_command(message: types.Message):
            from creator.telegram.event import help_message
            _message = await bot.reply_to(
                message,
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    escape_markdown(help_message()),
                    separator="\n"
                ),
                parse_mode="MarkdownV2"
            )

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        return bot
