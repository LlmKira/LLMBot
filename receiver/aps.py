# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午8:34
# @Author  : sudoskys
# @File    : aps.py
# @Software: PyCharm
import tzlocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler

job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None
}
SCHEDULER = AsyncIOScheduler(job_defaults=job_defaults, timezone=str(tzlocal.get_localzone()))


async def aps_start():
    SCHEDULER.start()
