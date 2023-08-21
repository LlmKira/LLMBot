# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 下午10:19
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

from cache.redis import cache
from schema import singleton
from sdk.utils import sync
from .schema import RouterCache, Router


@singleton
class RouterManager(object):
    def __init__(self):
        self.__redis_key__ = "router"
        self.router = sync(self._sync())

    async def _upload(self):
        return await cache.set_data(key=self.__redis_key__, value=self.router)

    async def _sync(self) -> RouterCache:
        _cache = await cache.read_data(key=self.__redis_key__)
        if not _cache:
            return RouterCache()
        try:
            sub_info = RouterCache().parse_obj(_cache)
        except Exception:
            raise Exception(f"not found router info")
        return sub_info

    def get_router_by_user(self, to_: str, user_id: int) -> List[Router]:
        _all = self.router.router
        return [router for router in _all if router.user_id == user_id and router.to_ == to_]

    def get_router_by_sender(self, from_: str) -> List[Router]:
        _all = self.router.router
        return [router for router in _all if router.from_ == from_]

    def add_router(self, router: Router):
        self.router.router.append(router)
        return sync(self._upload())
