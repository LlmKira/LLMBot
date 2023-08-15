# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:27
# @Author  : sudoskys
# @File    : controller.py
# @Software: PyCharm
import asyncio

from loguru import logger
from telebot import types
from telebot import util, formatting
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.formatting import escape_markdown

from app.setting import BotSetting

StepCache = StateMemoryStorage()


class BotRunner(object):
    def __init__(self):
        self.bot = None
        self.proxy = BotSetting.proxy_address

    def bot_create(self):
        self.bot = AsyncTeleBot(BotSetting.token, state_storage=StepCache)
        return self.bot

    def run(self):
        logger.info("Bot Start")
        bot = self.bot_create()
        if self.proxy:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy
            logger.info("Proxy tunnels are being used!")

        @bot.message_handler(commands='help', chat_types=['private', 'supergroup', 'group'])
        async def listen_help_command(message: types.Message):
            from app.event import help_message
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

        async def main():
            await asyncio.gather(
                bot.polling(non_stop=True, allowed_updates=util.update_types, skip_pending=True)
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
