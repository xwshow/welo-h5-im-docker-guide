# 轻量级 H5 即时通讯服务器配置与 PWA 离线推送避坑指南

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![Django](https://img.shields.io/badge/Django-Channels-092E20.svg)
![PWA](https://img.shields.io/badge/PWA-Web%20Push-orange.svg)

> **Lightweight H5 Instant Messaging & PWA Offline Push Starter Kit**  
> A minimal, runnable open-source architecture based on Django Channels, Redis, Nginx WebSocket reverse proxy, and Service Worker Web Push.

这是一份面向独立开发者、站长与前端工程师的 **可运行开源骨架**：内置最小化 H5 一对一文字 IM（Django + Channels）、生产级 Nginx WebSocket 反代配置、Redis 编排以及 PWA 离线推送前端模板。

项目旨在解决 H5 IM 部署中最常见的三大痛点：**WSS 长连接 60 秒断连、Nginx `Upgrade` 请求头丢失、移动端 PWA 离线通知唤醒**。

🔗 **在线体验 Demo**：[WeloIM 网页版即时通讯演示](https://www.weloim.com/)

---

## 📂 仓库目录结构

```text
.
├── README.md                         # 部署指南与架构避坑说明
├── LICENSE                           # MIT 开源协议
├── docker-compose.yml                # Redis + Nginx 一键编排模板
├── nginx/im-websocket.conf           # WebSocket / WSS 反向代理核心配置
├── pwa-push-demo/sw-push-template.js # PWA 离线推送 Service Worker 监听骨架
├── chat/                             # 最小 IM 核心逻辑（注册登录 / 好友 / 单聊 / WS）
├── im_guide/                         # Django ASGI 项目配置
├── templates/ + static/              # 移动端浏览器自适应聊天演示页
└── .env.example                      # 环境变量配置模板
```

## 🚀 本地 3 分钟快速启动

### 1. 启动后端与演示前端

```bash
python -m venv .venv
# Windows 激活环境: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt

# 初始化环境变量（Windows 请用 copy .env.example .env）
cp .env.example .env

python manage.py migrate
python manage.py runserver 0.0.0.0:2083
```

打开浏览器访问 [http://127.0.0.1:2083/](http://127.0.0.1:2083/)（建议使用手机模拟器模式体验）：

1. 注册两个测试账号  
2. 搜索并互相添加好友、通过验证  
3. 进入聊天窗口，体验实时双向收发消息  

### 2. 启动可选基础设施（Redis + Nginx）

```bash
docker compose up -d
# 启动后可通过 Nginx 入口访问: http://127.0.0.1:8080/（自动反代至本机 :2083）
```

生产环境建议：在 `.env` 中设置 `USE_REDIS=1` 与 `REDIS_URL=redis://127.0.0.1:6379/0`，使用 Daphne 或 Uvicorn 托管 ASGI 进程，并将 SSL/TLS 证书终止配置在 Nginx 层。

## 🛠️ 核心架构与部署避坑要点

### 1. 消息安全：严格遵循「先落库，再广播」

- **绝不信任客户端身份**：前端 WebSocket 帧携带的 `sender` 或 `user_id` 一律忽略，服务端仅通过认证后的 `scope["user"]` 绑定身份。
- **顺序不可逆**：服务端收到消息后必须执行 **写入数据库（Persist） → 触发频道广播（`group_send`）**，严禁先推后写，防止消息丢失或产生幻读。

### 2. Nginx 反向代理 WebSocket 防断连

完整配置见 [`nginx/im-websocket.conf`](nginx/im-websocket.conf)。部署时必须确保以下核心指令生效：

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_read_timeout 3600s;  # 防止 Nginx 默认 60 秒无数据传输主动掐断长连接
proxy_buffering off;       # 关闭代理缓冲，确保实时消息帧零延迟下发
```

### 3. PWA 离线推送与系统级唤醒

完整监听代码见 [`pwa-push-demo/sw-push-template.js`](pwa-push-demo/sw-push-template.js)：

- **`push` 事件**：浏览器处于后台甚至关闭标签页时，由 Service Worker 唤醒系统通知栏。
- **`notificationclick` 事件**：用户点击通知后，优先检索并聚焦已打开的聊天窗口（`clients.matchAll`），不存在则调用 `clients.openWindow` 拉起页面。
- **iOS 端特殊避坑**：iOS 16.4+ 支持 Web Push，但前提是用户必须通过 Safari 的「分享 → 添加到主屏幕」安装 PWA 后才能触发权限弹窗。

### 4. Channel Layer 选型

- **单机开发**：默认启用内存级 `InMemoryChannelLayer`，零依赖即可跑通。
- **多进程 / 分布式部署**：必须切换为 `channels_redis`，否则不同 Worker 进程之间的用户无法互相推送消息。

## 📌 开源骨架 vs 商业完整版说明

本仓库定位为轻量级技术验证与部署参考骨架，刻意保持代码精简：

- **已包含**：基础账号体系、好友关系链、一对一文本聊天、WebSocket 断线重连基础、PWA 推送前端模板。
- **未包含**：群组聊天与权限管理、富媒体（语音/图片/短视频）分片传输、消息已读回执与漫游同步、多端设备互踢、后台风控与敏感词过滤。

如果您正在寻找开箱即用、支持高并发与全套运营能力的成熟产品，欢迎了解完整方案：

- 🌐 产品官网与在线体验：[WeloIM 轻量级 H5 即时通讯平台](https://www.weloim.com/)
- 🏢 独立部署与源码授权：[WeloIM 企业级私有化部署方案](https://www.weloim.com/solutions/private-deployment/)

## 📄 License

本项目基于 [MIT License](LICENSE) 开源，您可以自由用于学习研究、二次开发或作为生产环境的服务器配置参考。

---

**企业级私有化部署**：[WeloIM 企业级私有化部署方案](https://www.weloim.com/solutions/private-deployment/) · **官网**：[WeloIM 轻量级 H5 即时通讯系统](https://www.weloim.com/)
