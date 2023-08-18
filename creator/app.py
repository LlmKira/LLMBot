# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:18
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio
import sys

from loguru import logger
from telebot import util

import plugins
from telegram import TelegramBotRunner

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True
           )

# 注册机器人事件
telegram_bot = TelegramBotRunner().telegram()

func = [telegram_bot.polling(non_stop=True, allowed_updates=util.update_types, skip_pending=False, timeout=60,
                             request_timeout=60)]

# 初始化插件系统
plugins.setup()


async def main():
    await asyncio.gather(
        *func
    )


for i in func:
    logger.success(f"Sender start:{i.__name__}")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
