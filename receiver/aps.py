# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午8:34
# @Author  : sudoskys
# @File    : aps.py
# @Software: PyCharm
import tzlocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None
}
SCHEDULER = BackgroundScheduler(job_defaults=job_defaults, timezone=str(tzlocal.get_localzone()))


async def aps_start():
    SCHEDULER.start()
