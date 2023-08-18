# 交换系统

我们的目标是实现一个类邮件的消息交换机系统，这个系统可以在不同的系统中进行消息的传递，同时可以在不同的系统中进行消息的回复。
接受消息的系统，我们称之为“接收者”，发送消息的系统，我们称之为“发送者”。
消息带有始地址和终地址，分配给 平台和 ID，采用通用的消息格式，可以在不同的系统中进行传递。

```
Telegram -> RabbitMQ -> Telegram
Rss -> RabbitMQ -> Telegram
Api -> RabbitMQ -> Telegram
```

由各种发送器提起请求，带上终末地址，交给 OpenAi的核心函数(end_user)，调用函数核心函数返回结果，然后通知过去。

任务产生 -> 任务队列 -> 任务处理 -> 任务队列 -> 任务消费

涉及跨进程通信，需要使用消息队列，消息队列的实现有很多，我们选择 RabbitMQ。

## 创建生产者还是

消费者就是平台数目，所以消费者是有限的。

生产者由平台的用户定义并创建，有多个。

可以一起绑定一个消息队列（订阅模式），也可以使用主题模式自动分流生产者的消息。

所以消费者队列和平台绑定。

## 认证

https://www.cnblogs.com/yanzhi-1996/articles/11115010.html#exchange%E6%A8%A1%E5%9E%8B

对于生产者，有两个分类：匿名生产者和认证生产者。匿名生产者如Rss 没有用户信息，认证生产者如Telegram有用户信息。
所以对于匿名生产者，我们需要在消息中加入用户信息，也就是Redis订阅列表。在生产消息的时候，乘订阅列表发送不同 tag 的消息。

订阅的数据类应该是这样的： 平台，Userid

```python
# 声明一个队列，用于接收消息
channel.queue_declare(queue='telegram', durable=True)
channel.basic_publish(exchange='',
                      routing_key='水许传',
                      body=Message()
                      )
```

## 中间件

Openai 作为消息中间件，修改消息并转发。
如果遇到了function, 则调用function，自身作为creator发送消息。