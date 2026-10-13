# HTTP、API、JSON、HTTPS 学习笔记
## 01 HTTP 请求 & 响应
### 问题1
标准HTTP请求和响应由哪些部分组成？
HTTP请求：
1. 请求行：请求方法 + URL + HTTP版本
2. 请求头（Header）：元信息，User-Agent、Content-Type、Cookie等
3. 请求体（Body）：POST/PUT携带的数据，GET一般没有body。

HTTP响应：
1. 状态行：HTTP版本 + 状态码 + 描述文字
2. 响应头（Response Header）
3. 响应体（Response Body）：返回给前端的数据（HTML、JSON）。

### 问题2
用户提交长篇笔记，GET还是POST？为什么？
POST。
原因：
1. GET参数放在URL里，长度有限制，长篇笔记放不下。
2. GET请求一般用于查询，不修改服务器数据；提交笔记属于新增数据，符合POST语义。
3. GET参数会保存在浏览器历史、日志，不适合传输大量业务数据。POST数据放在请求体。

### 问题3
HTTP状态码是什么？常见状态码，JotangNote项目哪里会用到？
状态码：服务器返回给客户端的数字编码，用来标识本次请求处理结果。
- 200 OK：请求成功。查询笔记成功。
- 201 Created：资源创建成功。新建笔记成功。
- 400 Bad Request：请求参数错误。提交笔记参数非法。
- 401 Unauthorized：未登录。用户未登录访问笔记。
- 403 Forbidden：权限不足。尝试查看别人私有笔记。
- 404 Not Found：资源不存在。访问不存在的笔记id。
- 422 Unprocessable Entity：参数校验失败。笔记内容校验不通过。
- 500 Internal Server Error：服务器内部代码异常。后端程序出错。

## 02 API/接口
### 问题
设计"获取某篇笔记详细内容"接口，需要考虑哪些内容？
1. 请求方式：GET，只做查询。
2. 路由路径：例如 `/api/note/{note_id}`，note_id为笔记唯一标识。
3. 权限校验：判断当前登录用户是否有权查看该笔记（私有/公开）。
4. 入参：note_id；可选：是否返回历史版本。
5. 返回数据结构：笔记标题、正文、创建时间、作者ID。
6. 异常处理：笔记不存在返回404；无权限返回403。
7. 缓存：热点笔记可查询Redis缓存，减少MySQL压力。
8. 数据过滤：防止敏感信息泄露。

## 03 JSON
### 问题1
JSON格式的数据长什么样？
JSON是纯文本，基础类型：对象`{}`、数组`[]`、字符串、数字、布尔、null。
示例：
```json
{
  "id": 1,
  "title": "第一篇笔记",
  "content": "Hello JotangNote"
}
```

### 问题2
Python如何把对象转为JSON，JSON转回对象？
内置库 `json`。
- `json.dumps()`：Python字典 → JSON字符串
- `json.loads()`：JSON字符串 → Python字典
FastAPI内部自动完成JSON序列化与反序列化。

## 04 HTTPS
### 问题
HTTPS加密过程是怎么样的？
HTTPS = HTTP + TLS/SSL。
1. TLS握手阶段：客户端和服务器协商加密套件，服务器下发证书，客户端验证证书合法性。双方协商生成会话密钥（对称密钥）。
2. 传输阶段：后续HTTP报文使用协商出来的对称密钥加密传输。
3. 作用：数据密文传输，中间人窃听只能拿到密文，无法篡改、查看明文。防止密码等敏感信息泄露。
