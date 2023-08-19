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

from schema import TaskHeader, RawMessage
from sdk.func_call import TOOL_MANAGER
from sdk.schema import Function
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
        bot = self.bot
        if self.proxy:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy
            logger.info("TelegramBot proxy_tunnels being used!")

        def is_command(text, command):
            if text.startswith(f"{command} "):
                return True
            if text == command:
                return True
            return False

        async def is_admin(message: types.Message):
            _got = await bot.get_chat_member(message.chat.id, message.from_user.id)
            return _got.status in ['administrator', 'creator']

        async def telegram_to_file(file):
            name = file.file_id
            _file_info = await bot.get_file(file.file_id)
            downloaded_file = await bot.download_file(_file_info.file_path)
            if isinstance(file, types.PhotoSize):
                name = f"{_file_info.file_id}.jpg"
            if isinstance(file, types.Document):
                name = file.file_name
            return await RawMessage.upload_file(name=name, data=downloaded_file)

        async def create_task(message: types.Message, funtion_enable: bool = False):
            _file = []
            if message.photo:
                _file.append(await telegram_to_file(message.photo[-1]))
            if message.document:
                if message.document.file_size < 1024 * 1024 * 10:
                    _file.append(await telegram_to_file(message.document))
            logger.info(f"telegram:create task from {message.chat.id} {message.text} funtion_enable:{funtion_enable}")
            return await TelegramTask.send_task(
                task=TaskHeader.from_telegram(
                    message,
                    file=_file,
                    task_meta=TaskHeader.Meta(function_enable=funtion_enable)
                )
            )

        @bot.message_handler(commands='bind', chat_types=['private'])
        async def listen_bind_command(message: types.Message):
            # TODO: 自动订阅系统
            return logger.warning("订阅系统")

        @bot.message_handler(content_types=['text', 'photo', 'document'], chat_types=['private'])
        async def handle_private_msg(message: types.Message):
            """
            自动响应私聊消息
            """
            message.text = message.text if message.text else message.caption
            if not message.text:
                return None
            if is_command(text=message.text, command="/task"):
                return await create_task(message, funtion_enable=True)
            if is_command(text=message.text, command="/tool"):
                _paper = ''
                _tool = TOOL_MANAGER.get_all_function()
                for name, c in _tool.items():
                    c: Function
                    _paper += f"{c.name} - {c.description}\n"
                return await bot.reply_to(
                    message,
                    text=formatting.format_text(
                        formatting.mbold("🔧 Tool List"),
                        escape_markdown(_paper),
                        separator="\n"
                    ),
                    parse_mode="MarkdownV2"
                )
            return await create_task(message, funtion_enable=False)

        @bot.message_handler(content_types=['text', 'photo', 'document'], chat_types=['supergroup', 'group'])
        async def handle_group_msg(message: types.Message):
            """
            自动响应群组消息
            """

            message.text = message.text if message.text else message.caption
            if not message.text:
                return None
            if is_command(text=message.text, command="/chat"):
                return await create_task(message, funtion_enable=False)
            if is_command(text=message.text, command="/task"):
                return await create_task(message, funtion_enable=True)
            if f"@{BotSetting.bot_username} " in message.text or message.text.endswith(f" @{BotSetting.bot_username}"):
                return await create_task(message, funtion_enable=False)

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
