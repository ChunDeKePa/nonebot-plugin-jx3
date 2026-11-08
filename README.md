<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-jx3

_基于 [NoneBot2](https://github.com/nonebot/nonebot2) 的剑网三（JX3）全功能 QQ 群助手插件，支持游戏数据查询与实时推送通知。_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/fuyang0811/nonebot-plugin-jx3.svg?cache=clear" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-jx3">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-jx3.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## ✨ 核心特性与二次开发优化

本项目基于开源社区项目二次开发与深度维护，进行了全方位的现代化重构与特性增强：

- **API 全面更新**：全面迁移适配至 [JX3API](https://www.jx3api.com) 最新官方规范接口，修复旧版路径失效与 404 问题，支持全功能查询与最新数据
- **模块化架构**：采用清晰的模块化分层设计，按职责拆分为独立子模块（`commands/`、`websocket/`、`templates/`）
- **现代化配置体系**：基于 Pydantic v2 提供类型安全配置，支持 `.env` 集中配置、权限分级与群白名单安全过滤
- **独立容器化支持**：原生适配 Docker 独立镜像打包，构建期固化 Playwright 浏览器内核与国内高速源，实现开箱即用与持久化存储
- **精美图片渲染**：升级 Jinja2 + HTML 模板与 Playwright 混合渲染链路，针对不同数据定制最佳视口与字体，输出更美观稳定
- **高可用推送系统**：优化 WebSocket 事件驱动架构，支持断线自动指数退避重连（5s~60s）与实时事件群组分发
- **数据本地持久化**：采用 TinyDB 轻量持久化存储，群服绑定与订阅数据独立保存于 `./data`，重启容器绝不丢失数据

## 功能概览

- **数据查询**：日常、金价、角色、心法、奇遇、招募、科举等 40+ 指令
- **实时推送**：奇遇、抓马、开服、新闻、攻防实况等 30+ 事件订阅
- **图片渲染**：所有查询结果以精美图片形式输出

## 🐳 Docker 容器化部署与运维指南（推荐）

本项目已完全内置标准 Docker 容器化环境与国内镜像加速支持（Debian 阿里源、pip 阿里/腾讯源、Playwright 淘宝镜像），并在构建期**预装固化了 Playwright Chromium 内核**，杜绝运行期二次下载。

配合 **NapCat Docker** 即可实现零 Python 本地环境、纯开箱即用的一键部署。

---

### 1. 首次部署步骤

#### ① 准备配置文件
复制环境变量模版生成 `.env` 配置文件：
```bash
cp .env.example .env
```
使用文本编辑器（如 `vim .env` 或 VS Code）修改关键参数：
- `SUPERUSERS`：机器人超级管理员 QQ 号列表，如 `SUPERUSERS=["10001"]`（拥有跨群绑定、全局订阅无视群管权限）
- `JX3_DEFAULT_SERVER`：默认服务器名称，如 `绝代天骄`
- `JX3_BOT_NAME`：机器人昵称，如 `水水`
- `JX3_ENABLED_GROUPS`：允许响应的群白名单（留空 `[]` 则所有群均可使用）

#### ② 一键编译并后台启动
在项目根目录下执行：
```bash
docker compose up -d --build
```
> **首次构建说明**：首次打包会安装系统字体、Python 依赖并下载 Playwright 浏览器内核（约 1~3 分钟）。后续更新代码由于启用了分层缓存，重新打包仅需数秒。

#### ③ 登录 NapCat 并配置反向 WebSocket
1. 打开浏览器访问 NapCat WebUI 管理面板：
   ```text
   http://你的服务器IP或localhost:6099/webui
   ```
2. 手机 QQ 扫描面板二维码登录机器人账号。
3. 进入 **「网络配置」** 页面，新建或编辑一条 **「反向 WebSocket」**：
   - **名称**：`nonebot`（可自定义）
   - **URL / 地址**：`ws://bot:8080/onebot/v11/ws`
     *(由于处于同一 docker compose 网络，直接使用容器名 `bot` 即可内网直连)*
   - **重连间隔**：`3000` (毫秒)
   - **启用**：勾选开启，点击保存。
4. 在已加入的 QQ 群中发送 `剑三帮助` 或 `日常`，机器人立即出图回复，部署成功！

---

### 2. 常用运维与重启指令速查

| 操作场景 | 推荐命令 | 说明 |
|---|---|---|
| **修改代码后重新打包** | `docker compose up -d --build bot` | 仅重新编译 bot 镜像并平滑重建容器，不影响 NapCat 登录状态 |
| **全量重新编译并启动** | `docker compose up -d --build` | 编译并启动所有服务 |
| **修改 `.env` 后的重启** | `docker compose restart bot` | `.env` 已采用只读卷挂载，直接重启即可生效，无需重新 build |
| **实时查看 Bot 运行日志** | `docker compose logs -f bot` | 查看实时收发消息、Matcher 匹配及报错调用栈 |
| **实时查看 NapCat 日志** | `docker compose logs -f napcat` | 查看 QQ 登录状态、心跳、网络连接日志 |
| **查看最后 100 行日志** | `docker compose logs --tail=100 bot` | 快速排查近期异常 |
| **停止所有服务** | `docker compose stop` | 仅暂停容器，保留运行状态与临时数据 |
| **彻底停止并删除容器** | `docker compose down` | 移除容器网络（持久化目录 `./data` 和 `./napcat` 会完整保留） |
| **检查容器运行状态与内存** | `docker compose ps` / `docker stats` | 检查 CPU、内存占用（已配置 1GB 共享内存防崩溃） |
| **进入 Bot 容器内部终端** | `docker compose exec bot bash` | 容器内手动排查环境或调试 |

---

### 3. 数据持久化机制说明

项目采用宿主机本地数据卷挂载，所有业务与登录数据**完全脱离容器生命周期**，即使执行 `docker compose down` 或重新 build，数据也绝不会丢失：

- `./data:/app/data`：**Bot 核心业务数据目录**
  - `jx3_bind.json`：各群服务器绑定数据（记录群号与区服对应关系）。
  - `jx3_subscribe.json`：各群订阅事件列表（如奇遇、开服、抓马等推送规则）。
- `./.env:/app/.env:ro`：**全局配置文件**，外部直接修改后执行 `docker compose restart bot` 秒级生效。
- `./napcat/config` 与 `./napcat/qq`：**NapCat 登录凭证与配置**，QQ 登录扫码一次即可长久免扫码自动登录。

---

### 4. docker-compose.yml 架构与配置详解

项目采用双容器轻量协同架构（`bot` + `napcat`），通过专用的内部 bridge 网络安全互联：

```
+-------------------------------------------------------------+
|                     宿主机 (Host Machine)                    |
|                                                             |
|   +-------------------+              +------------------+   |
|   |  napcat 容器       |              |  bot 容器        |   |
|   |  (QQ协议 / WebUI)  | --ws://bot-> |  (NoneBot2助手)  |   |
|   +-------------------+              +------------------+   |
|         |                                      |            |
|         v                                      v            |
|   ./napcat/ (登录态凭证)                 ./data/ (群绑定/订阅) |
|                                         ./.env (环境配置只读) |
+-------------------------------------------------------------+
```

#### 各服务核心配置解析：

1. **`bot` 服务（剑网三核心处理引擎）**
   - **`build` (`context: .`, `dockerfile: Dockerfile`)**：直接基于当前目录源码构建，镜像内已预装 Debian 阿里源、pip 加速源、中文字体以及 Chromium 浏览器内核。
   - **`shm_size: "1gb"`**：为 Playwright Chromium 渲染分配 1GB 共享内存（Docker 默认仅 64MB），彻底解决高并发或生成长图时浏览器由于内存溢出直接 Crash 的问题。
   - **`dns` (`223.5.5.5`, `119.29.29.29`)**：容器内固定指定阿里与腾讯公共 DNS，确保国内 API 及 WSS 推送长连接域名解析快速稳定。
   - **`ports: ["8080:8080"]`**：将 NoneBot 监听端口映射到宿主机，便于本地反代与调试。
   - **`volumes`**：
     - `./.env:/app/.env:ro`：只读挂载环境变量，宿主机随时修改配置无需重新打包镜像。
     - `./data:/app/data`：持久化 TinyDB 数据目录，保证群服绑定与订阅设置重启不丢。

2. **`napcat` 服务（QQ OneBot v11 协议客户端）**
   - **`image: mlikiowa/napcat-docker:latest`**：官方 NapCat 镜像，集成 WebUI 扫码控制面板。
   - **`ports: ["6099:6099"]`**：NapCat Web 控制台端口，浏览器打开直接进行手机 QQ 扫码认证。
   - **`depends_on: [bot]`**：容器启动顺序依赖，确保 Bot 就绪后再拉起 NapCat 建立连接。
   - **`volumes`**：
     - `./napcat/config` 与 `./napcat/qq`：持久化 QQ 设备指纹与登录 Ticket，扫码一次永久自动登录。
   - **`networks: [nonebot]`**：与 `bot` 处于同一虚拟局域网，WebUI 反向 WebSocket 地址直接填 `ws://bot:8080/onebot/v11/ws` 即可内网直连通信。

---

## 传统 Python 源码安装（本地开发）

如果你需要在本地直接以 Python 模式开发或集成到现有 NoneBot 实例：

```bash
nb plugin install nonebot-plugin-jx3
# 或
pip install nonebot-plugin-jx3
```

**运行依赖**：`nonebot2[fastapi]>=2.0.0`、`nonebot-adapter-onebot>=2.0.0`、`nonebot-plugin-apscheduler>=0.3.0`、`nonebot-plugin-htmlrender>=0.2.0,<0.8.0`、`playwright>=1.26.0`、`tinydb>=4.5.1`

本地环境需预先运行：
```bash
python -m playwright install --with-deps chromium
```

## 配置项速查表

在 `.env` 中按需配置：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `SUPERUSERS` | `["10001"]` | 超级管理员 QQ，不受群管限制，可在任意群进行绑定/订阅 |
| `COMMAND_START` | `["", "/"]` | 指令前缀，`""` 支持无前缀直接发词触发，如 `日常` |
| `JX3_DEFAULT_SERVER` | `绝代天骄` | 群未绑定时的兜底服务器 |
| `JX3_BOT_NAME` | `水水` | 渲染图片中显示的机器人昵称 |
| `JX3_ENABLED_GROUPS` | `[]` | 群白名单列表，`[]` 响应所有群；填入 `[123456]` 则仅白名单群可用 |
| `JX3API_BASE_URL` | `https://www.jx3api.com` | JX3API 官方 HTTP 数据接口 |
| `JX3_WSS_URL` | `wss://socket.nicemoe.cn` | JX3API 官方实时事件推送 WebSocket |
| `JX3API_TOKEN` | `""` | JX3API 会员 Token（VIP 数据接口鉴权） |
| `JX3_TUILAN_TICKET` | `""` | 推栏 Ticket（名剑大会 JJC 战绩、推栏配装必需） |
| `JX3WSS_TOKEN` | `""` | 推送 Token（购买付费推送后填入） |
| `RENDER_STORAGE_PATH`| `/root/.cache/ms-playwright` | Playwright 浏览器固化缓存路径 |

## 使用方法

### 初始设置（群管理员/群主）

```
绑定 <服务器名>     # 绑定本群服务器，例：绑定 绝代天骄
订阅               # 查看可订阅的推送列表
订阅 <名称>        # 开启订阅，例：订阅 奇遇
取消订阅 <名称>    # 关闭订阅
```

### 指令与功能一览

发送 **`帮助`** 或 **`剑三帮助`** 即可在群内实时获取最新的高清指令大图：

<div align="center">
  <img src="./DC7631D0218C87DB2C995BDD7718E9F0.png" width="750" alt="剑网三助手指令帮助大图" />
</div>

## 接口说明

- **免费接口**：无需任何 Token 即可直接使用（覆盖日常、开服、金价、科举等绝大部分基础指令）
- **VIP 接口**：需填写 `JX3API_TOKEN`（购买地址：[jx3api.com](https://www.jx3api.com)）
- **JJC 接口**：名剑大会战绩等特权数据额外需要 `JX3_TUILAN_TICKET`
- **推送功能**：基础广播无需额外配置；付费实时推送功能需配置 `JX3WSS_TOKEN`，WebSocket 支持断线指数退避自动重连（5s~60s）

## 致谢与声明

- 本项目基于开源社区 [nonebot-plugin-jx3](https://github.com/fuyang0811/nonebot-plugin-jx3) 项目二次开发并深度维护优化。
- 数据接口由 [JX3API](https://www.jx3api.com) 提供支持。
- 感谢开源社区所有贡献者与资源提供方。
