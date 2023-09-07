# -*- coding: utf-8 -*-
# @Time    : 2023/8/22 下午2:03
# @Author  : sudoskys
# @File    : bilibili.py
# @Software: PyCharm

import inscriptis
from loguru import logger
from pydantic import BaseModel

from middleware.user import SubManager, UserInfo
from schema import TaskHeader, RawMessage
from sdk.endpoint import openai
from sdk.endpoint.openai import Function
from sdk.func_call import BaseTool, listener
from sdk.schema import Message
from task import Task

__plugin_name__ = "search_in_bilibili"

bilibili = Function(name=__plugin_name__, description="Search videos on bilibili.com(哔哩哔哩)")
bilibili.add_property(
    property_name="keywords",
    property_description="Keywords entered in the search box",
    property_type="string",
    required=True
)


async def search_on_bilibili(keywords):
    from bilibili_api import search
    _result = await search.search_by_type(
        keyword=keywords,
        search_type=search.SearchObjectType.VIDEO,
        order_type=search.OrderVideo.TOTALRANK,
        page=1
    )
    _video_list = _result.get("result")
    if not _video_list:
        return "Search Not Success"
    _video_list = _video_list[:3]  # 只取前三
    _info = []
    for video in _video_list:
        _video_title = inscriptis.get_text(video.get("title"))
        _video_author = video.get("author")
        _video_url = video.get("arcurl")
        _video_tag = video.get("tag")
        _video_play = video.get("play")
        _video_info = f"(Title={_video_title},Author={_video_author},Link={_video_url},Tag={_video_tag},Love={_video_play})"
        _info.append(_video_info)
    return "\nHintData".join(_info)


class Bili(BaseModel):
    keywords: str

    class Config:
        extra = "allow"


@listener(function=bilibili)
class AlarmTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = True
    function: Function = bilibili
    keywords: list = ["哔哩哔哩", "b站", "B站", "视频", '搜索', '新闻', 'bilibili']

    def pre_check(self):
        try:
            import bilibili_api
            return True
        except ImportError as e:
            logger.error(f"plugin:package <bilibili_api> not installed:{e}")
            return False

    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        # 正则匹配
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        return None

    async def failed(self, platform, task, receiver, reason):
        try:
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    sender=task.sender,
                    receiver=receiver,
                    task_meta=TaskHeader.Meta(callback_forward=True,
                                              callback=TaskHeader.Meta.Callback(
                                                  role="function",
                                                  name=__plugin_name__
                                              ),
                                              ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text=f"🍖 {__plugin_name__}操作失败了！原因：{reason}"
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    @staticmethod
    async def llm_task(task, task_desc, raw_data):
        _submanager = SubManager(user_id=task.sender.user_id)
        driver = _submanager.llm_driver  # 由发送人承担接受者的成本
        model_name = "gpt-3.5-turbo-0613"
        endpoint = openai.Openai(
            config=driver,
            model=model_name,
            messages=Message.create_task_message_list(
                task_desc=task_desc,
                refer=raw_data
            ),
        )
        # 调用Openai
        result = await endpoint.create()
        _message = openai.Openai.parse_single_reply(response=result)
        _usage = openai.Openai.parse_usage(response=result)
        await _submanager.add_cost(
            cost=UserInfo.Cost(token_usage=_usage, token_uuid=driver.uuid, model_name=model_name)
        )
        return _message.content

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _set = Bili.parse_obj(arg)
            _search_result = await search_on_bilibili(_set.keywords)
            _question = task.message[0].text
            await Task(queue=receiver.platform).send_task(
                task=TaskHeader(
                    sender=task.sender,  # 继承发送者
                    receiver=receiver,  # 因为可能有转发，所以可以单配
                    task_meta=TaskHeader.Meta(
                        callback_forward=True,
                        reprocess_needed=True,
                        callback=TaskHeader.Meta.Callback(
                            role="function",
                            name=__plugin_name__
                        ),
                    ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text=_search_result
                        )
                    ]
                )
            )
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason=str(e))
