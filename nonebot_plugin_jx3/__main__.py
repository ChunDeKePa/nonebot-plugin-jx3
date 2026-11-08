"""包直接运行入口，支持通过 python -m nonebot_plugin_jx3 启动独立 Bot 服务"""
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from nonebot.plugin import get_plugin

# 1. 初始化 NoneBot 核心
try:
    driver = nonebot.get_driver()
except ValueError:
    nonebot.init()
    driver = nonebot.get_driver()

# 2. 注册 OneBot v11 协议适配器
try:
    driver.register_adapter(OneBotV11Adapter)
except Exception:
    pass

# 3. 确保本插件已注册到 NoneBot 插件管理器
if not get_plugin("nonebot_plugin_jx3"):
    nonebot.load_plugin("nonebot_plugin_jx3")

if __name__ == "__main__":
    nonebot.run()
