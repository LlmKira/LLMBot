# -*- coding: utf-8 -*-
# @Time    : 2023/8/18 下午6:11
# @Author  : sudoskys
# @File    : alarm.py
# @Software: PyCharm
import datetime

from loguru import logger
from pydantic import validator, BaseModel

from receiver.aps import SCHEDULER
from schema import TaskHeader, RawMessage
from sdk.endpoint.openai import Function
from sdk.func_call import BaseTool, listener
from task import Task

alarm = Function(name="set_alarm_reminder", description="Set a timed reminder")
alarm.add_property(
    property_name="delay",
    property_description="The delay time, in minutes",
    property_type="string",
    required=True
)
alarm.add_property(
    property_name="content",
    property_description="reminder content",
    property_type="string",
    required=True
)


class Alarm(BaseModel):
    delay: int
    content: str

    class Config:
        extra = "allow"

    @validator("delay")
    def delay_validator(cls, v):
        if v < 0:
            raise ValueError("delay must be greater than 0")
        return v


@listener(function=alarm)
class AlarmTool(BaseTool):
    """
    搜索工具
    """
    function: Function = alarm
    keywords: list = ["闹钟", "提醒", "定时", "到点", '分钟']

    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        return None

    async def failed(self, platform, receiver, reason):
        try:
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    receiver=receiver,
                    task_meta=TaskHeader.Meta(no_future_action=True,
                                              callback=TaskHeader.Meta.Callback(
                                                  role="function",
                                                  name="set_alarm_reminder"
                                              ),
                                              ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text="🍖 操作失败，原因：{}".format(reason)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    async def run(self, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _set = Alarm.parse_obj(arg)

            async def _send(receiver, _set):
                await Task(queue=receiver.platform).send_task(
                    task=TaskHeader(
                        receiver=receiver,
                        task_meta=TaskHeader.Meta(no_future_action=True,
                                                  callback=TaskHeader.Meta.Callback(
                                                      role="function",
                                                      name="set_alarm_reminder"
                                                  ),
                                                  ),
                        message=[
                            RawMessage(
                                user_id=receiver.user_id,
                                chat_id=receiver.chat_id,
                                text=_set.content
                            )
                        ]
                    )
                )

            logger.debug("set alarm {} minutes later".format(_set.delay))
            SCHEDULER.add_job(
                func=_send,
                trigger="date",
                run_date=datetime.datetime.now() + datetime.timedelta(minutes=_set.delay),
                args=[receiver, _set]
            )
            SCHEDULER.start()
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, receiver=receiver, reason=str(e))
