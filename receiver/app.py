# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午8:38
# @Author  : sudoskys
# @File    : app.py
# @Software: PyCharm
import asyncio

from loguru import logger

import plugins
from .function import FunctionReceiver
from .aps import aps_start
from .telegram import TelegramReceiver

func = [
    aps_start(),
    FunctionReceiver().function(),
    TelegramReceiver().telegram()
]

# 初始化插件系统
plugins.setup()


async def main():
    await asyncio.gather(
        *func
    )


for i in func:
    logger.success(f"Receiver start:{i.__name__}")
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
