# -*- coding: utf-8 -*-
import sys
from loguru import logger

from app.controller import BotRunner


logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")

# 日志机器
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="100 MB",
           enqueue=True
           )

App = BotRunner()
App.run()
