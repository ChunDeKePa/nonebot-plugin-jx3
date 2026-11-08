import os

# 确保 HTMLRender 渲染引擎指定为 playwright，且存储路径对齐内置缓存
os.environ.setdefault("RENDER_BACKEND", "playwright")
os.environ.setdefault("render_backend", "playwright")
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/root/.cache/ms-playwright")
os.environ.setdefault("RENDER_STORAGE_PATH", "/root/.cache/ms-playwright")
os.environ.setdefault("render_storage_path", "/root/.cache/ms-playwright")

import nonebot
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot import get_driver, require

# 自动初始化兼容：若作为独立程序启动尚未初始化 NoneBot，在此自动执行初始化并注册适配器
try:
    driver = get_driver()
except ValueError:
    nonebot.init(
        command_start=["", "/"],
        render_backend="playwright",
        render_storage_path="/root/.cache/ms-playwright",
    )
    driver = get_driver()
    try:
        from nonebot.adapters.onebot.v11 import Adapter as _OneBotV11Adapter
        driver.register_adapter(_OneBotV11Adapter)
    except Exception:
        pass

# 确保渲染后端属性存在
if not getattr(driver.config, "render_backend", None):
    try:
        setattr(driver.config, "render_backend", "playwright")
    except Exception:
        pass

# 确保依赖插件已加载
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_localstore")

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="剑网三助手",
    description="JX3API 全功能查询 + WebSocket 事件推送",
    usage="发送「剑三帮助」查看所有指令",
    type="application",
    homepage="https://github.com/fuyang0811/nonebot-plugin-jx3",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# 加载配置到模块级变量，供其他模块引用
driver = get_driver()
plugin_config = Config(**dict(driver.config))

# 将 plugin_config 注入到 config 模块，方便其他模块通过 from .config import plugin_config 访问
from . import config as _config_module
_config_module.plugin_config = plugin_config

# 导入所有命令模块（自动注册）
from . import commands  # noqa: F401


@driver.on_startup
async def startup():
    """启动时初始化 HTTP 客户端和 WebSocket 连接"""
    from .api_client import api_client
    from .websocket import client as ws_client

    await api_client.start()
    await ws_client.start()


@driver.on_shutdown
async def shutdown():
    """关闭时清理资源"""
    from .api_client import api_client
    from .websocket import client as ws_client

    await api_client.close()
    await ws_client.close()
