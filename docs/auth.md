# 授权

发送方的匿名使得权限管理变得困难，所以我们做如下设计：

1. 添加 sender 参数
2. 实行双向验权机制，(发送端验证订阅和权限（如果订阅+余额量就是可发） <- 自定义配置 -> 接收端拉取自定义配置)

难点：

1. 查询费率系统要完善。 ---> 中间件绑定计费系统
2. 绑定机制---> (平台:ID)

我们通过引入发送端计费 `SubManager` 进行计费，解决这章节的问题。

