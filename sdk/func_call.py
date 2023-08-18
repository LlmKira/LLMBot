# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午8:54
# @Author  : sudoskys
# @File    : func_call.py
# @Software: PyCharm
from abc import ABC, abstractmethod
from typing import Optional, Type, List

from loguru import logger
from pydantic import BaseModel

from .endpoint.openai import Function


class BaseTool(ABC, BaseModel):
    """
    基础工具类，所有工具类都应该继承此类
    """
    function: Function
    keywords: List[str]

    @abstractmethod
    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        if ...:
            return self.function
        else:
            return None

    @abstractmethod
    async def failed(self, platform, receiver, reason):
        return ...

    @abstractmethod
    async def run(self, receiver, arg, **kwargs):
        """
        处理message，返回message
        """
        return ...


class ToolManager:
    """
    工具管理器，用于管理所有工具
    """

    def __init__(self):
        self.__tool = {}
        self.__function = {}

    def add_tool(self, name: str, function: Function, tool: Type[BaseTool]):
        self.__tool[name] = tool
        self.__function[name] = function

    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        return self.__tool.get(name)

    def find_tool(self, tool: Type[BaseTool]) -> Optional[str]:
        for name, item in self.__tool.items():
            if item == tool:
                return name
        return None

    def get_function(self, name: str) -> Optional[Function]:
        return self.__function.get(name)

    def find_function(self, func: Function) -> Optional[str]:
        for name, function in self.__function.items():
            if function == func:
                return name
        return None

    def get_all_tool(self) -> dict:
        return self.__tool

    def get_all_function(self) -> dict:
        return self.__function

    def run_all_check(self, message_text) -> List[Function]:
        """
        运行所有工具的检查，返回所有检查通过的 函数
        """
        _pass = []
        for name, tool in self.get_all_tool().items():
            if tool().func_message(message_text=message_text):
                _pass.append(self.get_function(name))
        return _pass


TOOL_MANAGER = ToolManager()


def listener(function: Function):
    def decorator(func: Type[BaseTool]):
        if not isinstance(function, Function):
            raise TypeError(f"listener function must be Function, not {type(function)}")
        if not issubclass(func, BaseTool):
            raise TypeError(f"listener function must be subclass of BaseTool, not {func.__name__}")

        # 注册进工具管理器
        TOOL_MANAGER.add_tool(name=function.name, function=function, tool=func)
        logger.info(f"Function loaded success:{function.name}")

        def wrapper(*args, **kwargs):
            # 调用执行函数，中间人
            return func(**kwargs)

        return wrapper

    return decorator
