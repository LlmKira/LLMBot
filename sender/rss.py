# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 下午9:56
# @Author  : sudoskys
# @File    : rss.py
# @Software: PyCharm
import asyncio
import json
import socket

import feedparser
import html2text
from pydantic import BaseModel
from telebot import formatting

from cache.redis import cache
from middleware.router import RouterManager
from middleware.router.schema import router_set

__sender__ = "rss"

from schema import TaskHeader

from task import Task

router_set(role="sender", name=__sender__)


def sha1(string: str):
    import hashlib
    _sha1 = hashlib.sha1()
    _sha1.update(string.encode('utf-8'))
    return _sha1.hexdigest()[:10]


class RssApp(object):

    def parse_entry(self, entry):
        """
        {
                "title": entry["title"],
                "url": entry["link"],
                "id": entry["id"],
                "author": entry["author"],
                "summary": html2text.html2text(entry["summary"]),
            }
        """
        message = formatting.format_text(
            formatting.mbold(entry["title"]),
            formatting.escape_markdown(entry["summary"]),
            formatting.mlink(entry["author"], entry["url"]),
            separator="\n",
        )
        return message

    async def task(self):
        _router_list = RouterManager().get_router_by_sender(__sender__)
        for router in _router_list:
            try:
                _title, _entry = await Rss(feed_url=router.rules).get_updates()
                for item in _entry:
                    await Task(queue=router.to_).send_task(
                        task=TaskHeader.from_router(
                            from_=router.from_,
                            to_=router.to_,
                            user_id=router.user_id,
                            method=router.method,
                            message_text=self.parse_entry(item),
                        )
                    )
            except Exception as e:
                _title, _entry = f"Error When receive sub{router.rules}", []
                await Task(queue=router.to_).send_task(
                    task=TaskHeader.from_router(
                        from_=router.from_,
                        to_=router.to_,
                        user_id=router.user_id,
                        method=router.method,
                        message_text=_title,
                    )
                )
                continue

    async def rss_polling(self, interval=60 * 60 * 1):
        while True:
            await asyncio.sleep(interval)
            await self.task()


class Rss(object):
    """
    从缓存拉取，没有缓存就初始化，返回最后一条。
    有缓存则比对
    """

    class Update(BaseModel):
        title: str
        entry: dict

    def __init__(self, feed_url):
        # sha1
        self.db_key = f"rss:{sha1(feed_url)}"
        self.feed_url = feed_url

    def get_feed(self):
        socket.setdefaulttimeout(15)
        res = feedparser.parse(self.feed_url)
        try:
            json.dumps(res, indent=4, ensure_ascii=False)
        except Exception as e:
            raise ValueError("Fetch rss feed error")
        entries = res["entries"]
        _title = res["feed"]["title"]
        _entry = {}
        for entry in entries:
            _entry[entry["id"]] = {
                "title": entry["title"],
                "url": entry["link"],
                "id": entry["id"],
                "author": entry["author"],
                "summary": html2text.html2text(entry["summary"]),
            }
        return self.Update(title=_title, entry=_entry)

    async def re_init(self, update: Update) -> (str, list):
        _entry = list[update.entry.values()][:1]
        await cache.set_data(key=self.db_key, value=update.json(), timeout=60 * 60 * 60 * 7)
        return update.title, _entry

    async def update(self, cache_, update_, keys):
        _return = []
        for key in keys:
            # copy
            cache_.entry[key] = update_.entry[key]
            _return.append(update_.entry[key])
        await cache.set_data(key=self.db_key, value=cache_.json(), timeout=60 * 60 * 60 * 7)
        return update_.title, _return

    async def get_updates(self):
        _load = self.get_feed()
        _data = await cache.read_data(key=self.db_key)
        if not _data:
            return await self.re_init(_load)
        assert isinstance(_data, dict), "wrong rss data"
        _cache = self.Update.parse_obj(_data)
        # 验证是否全部不一样
        _old = list(_cache.entry.keys())
        _new = list(_load.entry.keys())
        _updates = [x for x in _new if x not in _old]
        # 全部不一样
        if len(_updates) == len(_new):
            return await self.re_init(_load)
        if len(_updates) == 0:
            return _load.title, []
        # 部分不一样
        return self.update(cache_=_cache, update_=_load, keys=_updates)
