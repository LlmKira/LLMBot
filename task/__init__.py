# -*- coding: utf-8 -*-
# @Time    : 2023/8/17 下午9:54
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import asyncio

import aio_pika
from aio_pika import Message, DeliveryMode
from loguru import logger

from schema import TaskHeader
from setting.task import RabbitMQSetting


# 用于通知消息变换（GPT 中间件）


class Task(object):
    def __init__(self, queue: str):
        """
        :param queue: 队列名字
        """
        self.queue_name = queue
        self.amqp_url = RabbitMQSetting.amqp_dsn

    async def send_task(self, task: TaskHeader):
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            channel = await connection.channel()
            message = Message(
                task.json(), delivery_mode=DeliveryMode.PERSISTENT,
            )
            # Sending the message
            await channel.default_exchange.publish(
                message, routing_key=self.queue_name,
            )
            logger.debug("生产者发送了任务：%r" % task.json())

    async def consuming_task(self, func: callable):
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            # Creating a channel
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)

            # Declaring queue
            queue = await channel.declare_queue(
                self.queue_name,
                durable=True,
            )
            await queue.consume(func)
            await asyncio.Future()  # run forever


"""

    def consuming_task(self, func: callable):
        def callback(ch, method, properties, body):
            logger.debug("消费者接收到了任务：%r" % body.decode("utf8"))
            _data = TaskHeader.parse_raw(body)

            def _ack():
                ch.basic_ack(delivery_tag=method.delivery_tag)

            func(_data, _ack)

        self.channel.basic_consume(on_message_callback=callback, queue=self.queue_name, auto_ack=False)
        self.channel.start_consuming()
"""
