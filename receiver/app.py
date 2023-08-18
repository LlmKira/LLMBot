# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio

from loguru import logger

from telegram import TelegramReceiver

func = [TelegramReceiver().telegram()]


async def main():
    await asyncio.gather(
        *func
    )

for i in func:
    logger.success(f"Receiver start:{i.__name__}")
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
