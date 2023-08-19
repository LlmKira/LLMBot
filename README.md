# LLMBot

LLMBot 是一款基于消息队列的机器人助手，可以装载插件完成许多功能。为 Gpt Func Call 和 广播机制的验证项目。

该 Bot 包含收发两端，可以跨平台使用。

## 📝 如何使用？

- 🛠 配置 `.env` 文件

```bash
cp .env.example .env
```

- ⚙️ 安装依赖

```bash
pip install -r requirements.txt
```

- 🗄 配置数据库环境

```bash
# 安装 Redis
apt-get install redis
systemctl enable redis.service --now
```

```bash
# 安装 RabbitMQ
docker pull rabbitmq:3.10-management
docker run -d -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=admin \
        -e RABBITMQ_DEFAULT_PASS=admin \
        --hostname myRabbit \
        --name rabbitmq \
        rabbitmq:3.10-management 
docker ps -l
```  

- ▶️ 运行

```bash
python3 creator/app.py
python3 receiver/app.py
```

## 基础命令

    /help - 帮助
    /chat - 聊天
    /task - 任务
    /tool - 工具列表
    /bind - 绑定发送人

## TODO

- [x] 插件系统
- [x] 定时系统
- [ ] 订阅系统
- [x] 插件的文件支持

## 💻 如何开发？

插件开发请参考 `plugins` 目录下的示例插件。

## 🤝 如何贡献？

欢迎提交 Pull Request，我们非常乐意接受您的贡献！请确保您的代码符合我们的代码规范，并附上详细的说明。感谢您的支持和贡献！ 😊
