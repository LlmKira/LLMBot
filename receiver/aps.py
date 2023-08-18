# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午8:34
# @Author  : sudoskys
# @File    : aps.py
# @Software: PyCharm
import tzlocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler

SCHEDULER = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))


async def aps_start():
    SCHEDULER.start()
