# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
from typing import Literal, Optional

from pydantic import BaseModel, root_validator, Field

from ...error import ValidationError


class Message(BaseModel):
    class FunctionCall(BaseModel):
        name: str
        arguments: str

    role: Literal["system", "assistant", "user", "function"] = "user"
    content: str
    # speaker
    name: Optional[str] = Field(None, description="speaker name", regex=r"^[a-zA-Z0-9_]+$")
    # AI generated function call
    function_call: Optional[FunctionCall] = None

    @root_validator
    def check(cls, values):
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        # 过滤value中的None
        return {k: v for k, v in values.items() if v is not None}


class Function(BaseModel):
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
