<div align="center">

# Onyx

### 一个零依赖的 Python 微 Web 框架 —— 路由、中间件、请求生命周期，全部用标准库实现

[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-000000)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-00AA00)](https://docs.python.org/3/library/)
[![Platform](https://img.shields.io/badge/platform-cross--platform-9cf)](https://github.com/WsNodeX/onyx)
[![Tests](https://img.shields.io/badge/tests-81%20passing-brightgreen)](https://github.com/WsNodeX/onyx/actions)
[![WSGI](https://img.shields.io/badge/WSGI-compatible-009688)](https://www.python.org/dev/peps/pep-3333/)

**开箱即用 · 无第三方依赖 · 自带离线测试客户端 · 标准库实现 WSGI**

[Why](#-为什么) · [Features](#-特性) · [Install](#-安装) · [Quick Start](#-快速开始) · [Architecture](#️-架构) · [API](#-接口一览) · [Roadmap](#-路线图) · [中文详解](#中文详解从零实现一个-web-框架)

</div>

---

## ✨ 为什么

市面上的 Web 框架要么"全家桶"（自带一大堆依赖、CLI、生态），要么需要你先读懂一堆抽象才能写第一行代码。
**Onyx 反其道而行**：它把"一个 HTTP 服务到底是怎么跑起来的"这件事，用最朴素的方式讲清楚——

- 没有 `pip install` 任何东西，标准库就够了；
- 没有隐藏的魔法，路由怎么匹配、中间件怎么串、异常怎么变响应，全部摊开在你面前；
- 自带一个**不发网络请求**的测试客户端，单元测试秒级跑完，CI 稳定。

它适合：想真正搞懂 Web 框架原理的人、需要轻量内嵌 HTTP 服务的工具、以及把"我会写框架"写进简历的练习。

## 🚀 特性

- **类型化路由**：`<id:int>` / `<amount:float>` / `<slug>` / `<path:path>` 四种参数转换器，编译成正则后精确匹配。
- **洋葱中间件**：类式与函数式都支持，注册顺序即执行顺序，进出对称。
- **错误即响应**：抛出 `NotFound` / `MethodNotAllowed` 等，框架自动转成带正确状态码与 `Allow` 头的响应；还能为任意异常注册专属处理器。
- **多种返回形态**：处理器可直接返回 `Response`、或 `dict` / `str` / `bytes`、或三元组 `(body, status, headers)`，框架帮你包好。
- **Blueprint 模块化**：用 URL 前缀把路由分组，再一次性注册，项目大了也不乱。
- **零依赖 WSGI**：`app` 本身就是一个合法的 WSGI 应用，可直接挂到 gunicorn / uwsgi；开发时也有内置单线程服务器兜底。
- **离线测试客户端**：`app.test_client()` 直接把请求喂进 `handle()`，不建 socket，测试又快又确定。
- **全平台、Python 3.9+**：`from __future__ import annotations` 保证老版本也能跑。

## 📦 安装

```bash
# 方式一：把 onyx/ 目录放进你的项目即可，无需安装
git clone https://github.com/WsNodeX/onyx.git
cp -r onyx/your_project/

# 方式二：作为可编辑包安装
pip install -e .
```

> 没有任何运行时依赖。只要有一份 Python 3.9+ 解释器就能跑。

## ⚡ 快速开始

```python
# app.py
from onyx import Onyx, Response

app = Onyx(name="hello")


@app.get("/")
def index(request):
    return Response.text("Hello, Onyx!")


@app.get("/users/<id:int>")
def user(request):
    uid = request.path_params["id"]
    return Response.json({"id": uid, "name": f"user-{uid}"})


if __name__ == "__main__":
    app.run(port=8000)
```

运行：

```bash
python app.py
# 或
python -m onyx run app:app --port 8000
```

预期输出（访问 `http://127.0.0.1:8000/users/7`）：

```json
{"id": 7, "name": "user-7"}
```

访问根路径 `http://127.0.0.1:8000/` 会得到：

```
Hello, Onyx!
```

离线测试（不发网络请求）：

```python
from app import app

client = app.test_client()
assert client.get("/users/7").json() == {"id": 7, "name": "user-7"}
assert client.get("/users/abc").status_code == 404
```

仓库里 `examples/demo_app.py` 是一个更完整的示例（TODO API + 鉴权 Blueprint），可直接 `python examples/server.py` 运行。

## 🏗️ 架构

一次请求在 Onyx 中的完整生命周期：

```
        ┌─────────────────────────────────────────────┐
        │                 HTTP 客户端                   │
        └───────────────┬─────────────────────────────┘
                        │  GET /users/7
                        ▼
        ┌─────────────────────────────────────────────┐
        │       WSGI 入口 / 内置开发服务器              │
        │   (app.__call__ 或 server.make_server)        │
        └───────────────┬─────────────────────────────┘
                        │  构建 Request 对象
                        ▼
        ┌─────────────────────────────────────────────┐
        │  Onyx.handle(request)                         │
        │                                               │
        │   1. Router.resolve(method, path)             │
        │        └─ 命中路由 → 拿到 handler + 路径参数   │
        │   2. Middleware 链 包裹 handler                │
        │        └─ 外层 → 内层 → handler → 内层 → 外层 │
        │   3. handler 返回 (Response / dict / str …)   │
        │   4. _ensure_response 统一包装成 Response      │
        │   5. 异常 → HTTPError → 正确状态码响应         │
        └───────────────┬─────────────────────────────┘
                        │  Response(status, headers, body)
                        ▼
        ┌─────────────────────────────────────────────┐
        │            写回 HTTP 响应                      │
        └─────────────────────────────────────────────┘
```

模块分层：

```
onyx/
├── app.py          Onyx 应用：路由注册、中间件、错误处理、WSGI、测试客户端
├── router.py       路由编译（<name:type> → 正则）与 (method, path) 解析
├── request.py      Request：懒解析 query / json / form / cookies
├── response.py     Response：json/text/html/redirect + Set-Cookie
├── middleware.py   中间件基类与洋葱链构建
├── blueprint.py    带 URL 前缀的路由分组
├── errors.py       HTTPError 体系（400/401/403/404/405/422/500…）
├── datastructures.py  大小写无关 Headers、MultiDict、Cookie 编解码
├── server.py       零依赖开发服务器（http.server 封装）
├── testing.py      不发网络的 TestClient
└── __main__.py     CLI：python -m onyx run module:app
```

## 🔌 接口一览

| 能力 | 用法 | 说明 |
| --- | --- | --- |
| 应用 | `Onyx(name=...)` | 框架核心对象 |
| 路由装饰器 | `@app.get` `@app.post` `@app.put` `@app.delete` `@app.patch` `@app.route` | 注册处理器 |
| 路径参数 | `/users/<id:int>` | `int` / `float` / `str`(默认) / `path` |
| 中间件 | `app.add_middleware(M)` / `@app.use` | 类式或函数式 |
| 错误处理 | `@app.errorhandler(NotFound)` | 为某类异常定制响应 |
| 返回 | `Response` / `dict` / `str` / `bytes` / `(body, status, headers)` | 自动包装 |
| Blueprint | `Blueprint("api", url_prefix="/api")` | 模块化路由 |
| 测试 | `app.test_client().get(...)` | 离线、确定性 |
| 运行 | `app.run(port=8000)` / `python -m onyx run pkg:app` | 开发服务器 |
| 生产 | 把 `app` 当 WSGI 应用交给 gunicorn 等 | 标准兼容 |

`Request` 常用属性：`method`、`path`、`query`(MultiDict)、`path_params`、`json`、`form`、`cookies`、`headers`、`body`。

`Response` 常用构造：`Response.text()`、`Response.json()`、`Response.html()`、`Response.redirect()`、`resp.set_cookie()`。

## 🧭 路线图

- [ ] 静态文件服务（`app.static(prefix, dir)` 与 `Range` 支持）
- [ ] 表单 `multipart/form-data` 解析
- [ ] OpenAPI / Swagger 文档自动生成
- [ ] 异步处理器支持（`async def` + ASGI 入口）
- [ ] 限流、CORS、压缩等常用中间件内置
- [ ] 模板引擎适配层（适配 Jinja2 等外部实现）
- [ ] 更细粒度的路由 `name` 反向生成 URL

## 🤝 贡献

欢迎提 Issue 与 PR。本地开发：

```bash
git clone https://github.com/WsNodeX/onyx.git
cd onyx
python -m unittest discover -s tests   # 81 个测试应全过
```

提交前请确保测试通过；新功能请附带测试与文档。

## 📄 License

[MIT](LICENSE) © WsNodeX

---

# 中文详解：从零实现一个 Web 框架

> 下面是一篇可以直接发到掘金 / 知乎 / 小红书 / B 站的技术科普文底稿。它讲清了 Onyx 解决什么问题、核心原理、实现要点、横向对比和扩展方式，读者视角，不只是一份 API 清单。文末附"如何把它扩展成一篇发布稿"的提示。

## 一、痛点：我们到底为什么需要"自己写一个"框架？

几乎所有 Python 后端入门都会从 Flask 或 FastAPI 开始。它们很好用，但有一个副作用：**用久了，你会写路由、写依赖注入，却说不清一个请求从网卡到你的函数到底经历了什么。**

面试时常被追问：

- "路由 `<int:id>` 是怎么解析的？正则怎么生成的？"
- "中间件为什么叫洋葱模型？进出顺序是怎样的？"
- "抛出一个异常，怎么就变成了带正确状态码的 HTTP 响应？"
- "为什么需要一个不发网络请求的测试客户端？"

这些问题，光用框架是答不出的——你得自己写过一遍才知道。**Onyx 就是我为了把这些问题彻底想明白，而手搓的一个零依赖框架。** 它不追求替代 Flask，而是追求"每一行都看得懂、改得了、讲得清"。

更重要的是：**零依赖**。整个框架只用到 Python 标准库。这意味着它能在任何装了 Python 的机器上跑，不担心版本冲突，也方便你把它内嵌进任何工具里当 HTTP 服务用。

## 二、核心原理：一次请求的生命周期

Onyx 的核心只有一句话：**把 HTTP 请求变成 `Request` 对象，经过"路由→中间件→处理器"，再变回 `Response` 对象。**

完整链路是：

1. **接入层**：生产环境里 `app` 是个标准 WSGI 应用，可以直接交给 gunicorn；开发时 Onyx 用标准库的 `http.server` 包了一个小服务器帮你起服务。
2. **构建 Request**：从环境变量或原始连接里取出方法、路径、查询串、请求头、body，封装成 `Request`。
3. **路由解析**：`Router.resolve(method, path)` 先看路径能不能匹配到某条路由；匹配到了但方法不对，返回 **405 + `Allow` 头**（告诉你允许哪些方法）；完全不匹配，返回 **404**。
4. **中间件链**：把注册的中间件一层层包在处理器外面，形成"洋葱"——请求从外到内穿过中间件，响应从内到外再穿回来。
5. **处理器执行**：你的函数拿到 `Request`，返回任意形态（Response / dict / str / bytes / 三元组），框架统一包成 `Response`。
6. **异常兜底**：处理器里抛出 `NotFound` 之类的 `HTTPError`，会被捕获并转成对应状态码的 JSON 响应；没注册的异常则统一成 500，绝不会让服务器崩溃。

这套流程代码量不大，但把"Web 框架到底在干什么"讲得清清楚楚。

## 三、几个关键实现点（面试常问）

**1. 路由是怎么编译的？**
`<id:int>` 这种写法，本质是字符串模板。Onyx 用正则把它拆开：`int` 对应 `\d+`，`float` 对应 `\d+(?:\.\d+)?`，`path` 对应 `.+?`（能吃下斜杠），默认 `str` 对应 `[^/]+`。每个参数还记下它的类型，匹配成功后把字符串当场转成 `int` / `float`，直接放进 `request.path_params`，你的代码拿到就是真类型，不用自己 `int()`。

**2. 中间件为什么是"洋葱"？**
核心是这一行链式包裹：`chain = build_chain(middlewares, handler)`。它从最外层中间件开始，把"下一个调用"一层层传进去。所以第一个注册的中间件最先看到请求、最后看到响应——天然对称，非常适合做"计时""日志""跨域""鉴权"。

**3. 错误怎么变成响应？**
所有错误都继承自 `HTTPError`，每个子类自带 `status_code`。`handle()` 里用 `try/except HTTPError` 兜住，自动渲染成 `{"error": "...", "detail": "..."}` 的 JSON，并带上该有的头（比如 405 的 `Allow`）。你还能用 `@app.errorhandler(NotFound)` 给某类错误定制专属响应，比如返回更好看的错误页。

**4. 为什么需要"不发网络"的测试客户端？**
很多框架的测试要真起端口、发 HTTP，慢且不稳定。Onyx 的 `TestClient` 直接把请求构造好、喂进 `handle()`，等于绕过了网络层，但中间件、路由、异常处理一条不落都跑到了。于是 81 个测试秒级跑完，CI 永远绿。

## 四、和主流框架的对比

| 维度 | Onyx | Flask | FastAPI |
| --- | --- | --- | --- |
| 运行时依赖 | **0（纯标准库）** | 较少（Werkzeug 等） | 较多（Starlette/Pydantic） |
| 类型提示 / 自动校验 | 路由类型转换 | 自行处理 | 强（Pydantic） |
| 异步支持 | 暂为同步 | 同步 | 原生 async |
| 学习成本 | 极低（代码可读） | 低 | 中 |
| 生产就绪 | WSGI 兼容，可挂 gunicorn | 成熟 | 成熟 |
| 适合场景 | 学原理 / 内嵌服务 / 轻量 API | 通用 Web | 数据 API / AI 服务 |

一句话：**Onyx 不是来抢饭碗的，是来帮你把 Flask/FastAPI 背后那层"黑盒"拆开看明白的。** 看懂它，再去用任何框架都会更踏实。

## 五、怎么扩展（从玩具到能用的几步）

- **加鉴权**：写一个 `AuthMiddleware`（类式中间件），在 `handle` 里校验 `Authorization` 头，失败就 `raise Unauthorized()`，响应自动变 401。
- **接数据库 / ORM**：在处理器里正常 `import` 你的 SQLAlchemy / 自研 DAO 即可，Onyx 不绑定任何持久层。
- **出 OpenAPI 文档**：遍历 `app.router._routes`，把每条路由的方法、路径参数、处理器签名收集起来，就能自动生成 Swagger JSON。
- **上生产**：`gunicorn app:app` 即可，因为 `app` 本身就是合法 WSGI 应用；想更高并发就上 uwsgi / 多 worker。

## 六、如何把本文扩展成一篇发布稿（提示）

- **标题方向**：《我用 800 行标准库，手搓了一个能跑的 Web 框架》/《面试被问"框架原理"，我直接写了一个》/《零依赖不是噱头：从路由正则到洋葱中间件》。
- **开头钩子**：先抛一个真实面试/踩坑场景，再引出"不如自己写一个"。
- **结构建议**：原理图（就是上面那张 ASCII）→ 分段代码 + 运行结果 → 对比表 → "你能从中学到什么"。
- **配图**：把架构图、一次请求时序画成图（可放仓库后用 jsDelivr 引用，注意用 `https://cdn.jsdelivr.net/gh/WsNodeX/onyx@main/...` 绝对地址）。
- **结尾**：引导读者 clone 仓库跑测试，留下"下一篇写 X"的钩子，促进关注。

---

*Onyx —— 把"Web 框架"这件看起来很高深的事，拆成你也能一行行写出来的样子。*
