# -*- coding: utf-8 -*-
# Source: https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/utilities/redis.py
from __future__ import annotations

import json

import redis
from loguru import logger
from pydantic import BaseSettings, Field, root_validator

from sdk.schema import Message
from .utils import get_client


class RedisChatMessageHistory(object):
    class RedisSettings(BaseSettings):
        redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
        redis_key_prefix: str = "llm_message_store_0:"

        class Config:
            env_file = '.env'
            env_file_encoding = 'utf-8'

        @root_validator
        def redis_is_connected(cls, values):
            redis_url = values.get("redis_url")
            try:
                get_client(redis_url=redis_url)
            except redis.exceptions.ConnectionError as error:
                logger.error(error)
                raise ValueError("Could not connect to Redis")
            else:
                logger.success("Redis connect success")
            return values

    def __init__(
            self,
            session_id: str,
            ttl: int,
            redis_config: RedisSettings = RedisSettings(),
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Could not import redis python package. "
                "Please install it with `pip install redis`."
            )

        try:
            self.redis_client = get_client(redis_url=redis_config.redis_url)
        except redis.exceptions.ConnectionError as error:
            logger.error(error)

        self.session_id = session_id
        self.key_prefix = redis_config.redis_key_prefix
        self.ttl = ttl

    @property
    def key(self) -> str:
        """Construct the record key to use"""
        return self.key_prefix + self.session_id

    @property
    def messages(self) -> List[Message]:  # type: ignore
        """Retrieve the messages from Redis"""
        _items = self.redis_client.lrange(self.key, 0, -1)
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]
        messages = [Message.parse_obj(m) for m in items]
        return messages

    def add_message(self, message: Message) -> None:
        """Append the message to the record in Redis"""
        self.redis_client.lpush(self.key, message.json())
        if self.ttl:
            self.redis_client.expire(self.key, self.ttl)

    def clear(self) -> None:
        """Clear session memory from Redis"""
        self.redis_client.delete(self.key)
