# -*- coding: utf-8 -*-
# @Time    : 2023/8/15 下午10:34
# @Author  : sudoskys
# @File    : base.py
# @Software: PyCharm
from typing import Union, List, Optional, Literal

from pydantic import BaseModel, root_validator, validator, Field

from .action import Tokenizer, TokenizerObj
from .schema import Message, Function
from ...error import ValidationError
from ...network import request

MODEL = Literal[
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo",
    "gpt-4-0314",
    "gpt-4-0613",
    "gpt-4"]


class Openai(BaseModel):
    class Driver(BaseModel):
        endpoint: str = Field("https://api.openai.com/v1/chat/completions", env='OPENAI_API_ENDPOINT')
        api_key: str = Field(None, env='OPENAI_API_KEY')
        proxy_address: str = Field(None, env="OPENAI_API_PROXY")  # "all://127.0.0.1:7890"
        token: Tokenizer = TokenizerObj

        @validator("api_key")
        def check_api_key(self, v):
            if v:
                if not str(v).startswith("sk-"):
                    raise ValidationError("api_key must start with `sk-`")
            return v

        class Config:
            env_file = '.env'
            env_file_encoding = 'utf-8'

    config: Driver
    model: MODEL = "gpt-3.5-turbo"
    message: List[Message]
    function: Optional[List[Function]] = None
    function_call: Optional[str] = None
    """
    # If you want to force the model to call a specific function you can do so by setting function_call: {"name": "<insert-function-name>"}. 
    # You can also force the model to generate a user-facing message by setting function_call: "none". 
    # Note that the default behavior (function_call: "auto") is for the model to decide on its own whether to call a function and if so which function to call.
    """

    temperature: Optional[float] = 1
    top_p: Optional[float] = None
    n: Optional[int] = 1
    # Bot于流式响应负载能力有限
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[dict] = None
    user: Optional[str] = None

    # 用于调试
    echo: Optional[bool] = False

    def update_model(self, model: MODEL = "gpt-3.5-turbo"):
        self.model = model

    @staticmethod
    def get_model_list():
        return MODEL.__args__

    @staticmethod
    def get_max_token(model: str):
        v = 2048
        if "gpt-3.5" in model:
            v = 4096
        elif "gpt-4" in model:
            v = 8192
        if "-16k" in model:
            v = v * 4
        elif "-32k" in model:
            v = v * 4
        return v

    @validator("max_tokens")
    def update_max_tokens(self, v):
        """
        自动更新max_tokens
        """
        if not v:
            v = self.get_max_token(self.model)
        return v

    @validator("presence_penalty")
    def check_presence_penalty(self, v):
        if not (2 > v > -2):
            raise ValidationError("presence_penalty must be between -2 and 2")
        return v

    @validator("stop")
    def check_stop(self, v):
        if isinstance(v, list) and len(v) > 4:
            raise ValidationError("stop list length must be less than 4")
        return v

    @validator("temperature")
    def check_temperature(self, v):
        if not (2 > v > 0):
            raise ValidationError("temperature must be between 0 and 2")
        return v

    @root_validator
    def check(self, values):
        if values.get("function"):
            if values.get("model") not in ["gpt-3.5-turbo-0613", "gpt-4-0314", "gpt-4-0613", "gpt-4"]:
                raise ValidationError("function only support model: gpt-3.5-turbo-0613, gpt-4-0314, gpt-4-0613, gpt-4")
        return values

    @validator("message")
    def check_message(self, v):
        num_tokens_from_messages = TokenizerObj.num_tokens_from_messages(v, model=self.model)
        if num_tokens_from_messages > self.max_tokens:
            raise ValidationError("messages num_tokens > max_tokens")

    async def create(self,
                     **kwargs
                     ):
        """
        请求
        :return:
        """
        """
        curl https://api.openai.com/v1/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -d '{"model": "text-davinci-003", "prompt": "Say this is a test", "temperature": 0, "max_tokens": 7}'
        """
        # Clear tokenizer encode cache
        # TokenizerObj.clear_cache()
        # 返回请求
        return await request(
            method="POST",
            url=self.config.endpoint,
            data=self.dict(exclude_none=True, exclude={"config", "echo"}),
            headers={
                "User-Agent": "Mozilla/5.0",
                "api-key": f"Bearer {self.config.api_key}"
            },
            proxy=self.config.proxy_address,
            json_body=True
        )
