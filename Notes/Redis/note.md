# Redis 学习笔记
## 问题1
Redis为什么这么快？
1. 数据全部放在内存，内存读写速度远高于磁盘，没有磁盘IO瓶颈。
2. 单线程模型：避免多线程竞争锁带来的开销，没有线程切换损耗。
3. IO多路复用，高效处理大量并发网络连接。
4. 底层数据结构高度优化（哈希表、跳表等）。
5. 协议简单，解析开销很小。

## 问题2
在MySQL中的一行数据，你可以以什么样的形式存到Redis中作为缓存？
推荐使用Hash（哈希结构）存储。
例如用户笔记：key = `note:1001`，hash字段：title、content、create_time、user_id。
也可以序列化为JSON字符串，以String类型存储。
读取流程：先查Redis，命中直接返回；未命中再查询MySQL，查询完成后回写Redis。

## 问题3
如何使用你所选择的编程语言来通过代码操作Redis？
使用 redis-py 库。
1. 安装：pip install redis
2. 创建Redis客户端，填写IP、端口
3. 调用方法：hset/hget（哈希）、set/get（字符串）等读写命令。
