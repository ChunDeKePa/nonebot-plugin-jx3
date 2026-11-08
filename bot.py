"""NoneBot2 独立服务启动脚本"""
import os

# 确保 HTMLRender 渲染引擎指定为 playwright，且存储路径对齐内置缓存
os.environ.setdefault("RENDER_BACKEND", "playwright")
os.environ.setdefault("render_backend", "playwright")
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/root/.cache/ms-playwright")
os.environ.setdefault("RENDER_STORAGE_PATH", "/root/.cache/ms-playwright")
os.environ.setdefault("render_storage_path", "/root/.cache/ms-playwright")

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 1. 初始化 NoneBot 核心（支持空前缀与斜杠前缀，显式指定渲染后端为 playwright）
nonebot.init(
    command_start=["", "/"],
    render_backend="playwright",
    render_storage_path="/root/.cache/ms-playwright",
)

# 2. 注册 OneBot v11 协议适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 3. 加载剑网三助手插件
nonebot.load_plugin("nonebot_plugin_jx3")

if __name__ == "__main__":
    nonebot.run()
