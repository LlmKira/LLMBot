# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
from typing import Literal, Optional

from pydantic import BaseModel, root_validator, Field

from sdk.error import ValidationError


class Message(BaseModel):
    class FunctionCall(BaseModel):
        name: str
        arguments: str

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: str
    # speaker
    name: Optional[str] = Field(None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    # AI generated function call
    function_call: Optional[FunctionCall] = None

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}


class Function(BaseModel):
    """
    函数定义体。
    供外部模组定义并注册函数
    """

    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}

    name: str
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")
    required: list[str] = []

    def add_property(self, property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.required.append(property_name)

    def parse_schema_to_properties(self, schema: BaseModel):
        """
        解析pydantic的schema
        传入一个pydantic的schema，解析成properties
        参数可以被数据模型所定义
        """
        self.parameters.properties = schema.schema()["properties"]
