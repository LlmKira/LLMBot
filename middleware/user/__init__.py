# -*- coding: utf-8 -*-
# @Time    : 2023/8/21 上午12:06
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from loguru import logger

from cache.redis import cache
from schema import singleton
from sdk.utils import sync
from .schema import UserInfo


@singleton
class SubManager(object):
    def __init__(self, user_id: int):
        self.reload_exception = None
        self.sub_info: UserInfo = sync(self._sync(user_id=user_id))
        assert isinstance(self.sub_info, UserInfo) is not True, "sub info error"

    async def _upload(self, user_id: int, ignore_exception=False):
        if self.reload_exception and not ignore_exception:
            logger.warning(f"you are upload a default sub info for {user_id} to wipe out the original data")
            return None
        await cache.set_data(key=f"sub:{user_id}", value=self.sub_info.json())

    async def _sync(self, user_id: int):
        _cache = await cache.read_data(key=f"sub:{user_id}")
        if not _cache:
            return UserInfo(user_id=user_id)
        try:
            sub_info = UserInfo().parse_obj(_cache)
        except Exception as e:
            self.reload_exception = True
            logger.warning(f"not found sub info {user_id},{e}")
            return UserInfo(user_id=user_id)
        return sub_info

    def llm_driver(self):
        return self.sub_info.llm_driver

    async def block_plugin(self, plugin_name: str):
        self.sub_info.plugin_subs.lock.append(plugin_name)
        return self.sub_info.plugin_subs.lock

    async def get_lock_plugin(self):
        return self.sub_info.plugin_subs.lock

    async def add_cost(self, cost: UserInfo.Cost) -> list:
        self.sub_info.costs.append(cost)
        await self._upload(user_id=self.sub_info.user_id)
        return self.sub_info.costs

    async def get_total_cost(self) -> int:
        return self.sub_info.total_cost()

    async def get_cost_by_function_name(self, function_name: str) -> list:
        return [cost for cost in self.sub_info.costs if cost.function_name == function_name]
