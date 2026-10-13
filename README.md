# JotangNote 项目

## 项目简介

基于 Python + FastAPI 搭建简易 Web 服务演示。
项目目录结构：

```
JotangNote/
├── Notes/           # 文档、截图存放目录
│   └── Env/         # 运行截图
└── Project/
    └── src/         # 源代码文件夹
        ├── hello_terminal.py  # 控制台打印demo
        └── web_server.py      # FastAPI Web接口demo
```

### 1. hello_terminal.py

功能：控制台输出一行文本，验证本地 Python 环境正常。
运行命令：

```
python hello_terminal.py
```

输出：Hello World From Terminal!

### 2. web_server.py

功能：启动 Web 服务，提供 GET 接口 /hello
依赖：fastapi, uvicorn
安装依赖：

```
pip install fastapi uvicorn
```

启动命令：

```
python web_server.py
```

访问地址：http://127.0.0.1:8080/hello

#### web_server.py 代码说明

- FastAPI：Web 后端框架，用于快速开发接口
- uvicorn：ASGI 服务器，负责监听端口，处理网络请求
- @app.get ("/hello")：注册 GET 接口，访问该路径执行 hello 函数
- if **name** == "**main**"：文件直接运行时启动 web 服务；被其他文件导入时不启动服务
