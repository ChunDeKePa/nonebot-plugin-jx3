"""commands/subscribe.py — 订阅管理指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg

from ..utils import group_filter
from ..database import db


# ===== 订阅 =====
cmd_subscribe = on_command(
    "订阅", rule=group_filter(), priority=5, block=True,
    permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN
)


@cmd_subscribe.handle()
async def handle_subscribe(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()

    if not name:
        # 无参数：显示订阅列表
        current = await db.get_subscribes(event.group_id)
        # 排除别名去重展示
        show_available = [n for n in db.SUBSCRIBE_NAMES if n not in current and n != "八卦"]
        msg = f"📋 本群已订阅：{', '.join(current) if current else '无'}\n"
        msg += f"📝 可订阅列表：{', '.join(show_available)}"
        await cmd_subscribe.finish(msg)

    if name == "八卦":
        name = "818"

    # 有参数：添加订阅
    if name not in db.SUBSCRIBE_NAMES:
        await cmd_subscribe.finish(
            f"❌ 无效的订阅名称：{name}\n"
            f"📝 可订阅列表：{', '.join([n for n in db.SUBSCRIBE_NAMES if n != '八卦'])}"
        )

    success = await db.add_subscribe(event.group_id, name)
    if success:
        await cmd_subscribe.finish(f"✅ 订阅【{name}】成功")
    else:
        await cmd_subscribe.finish(f"⚠️ 已订阅【{name}】，无需重复订阅")


# ===== 取消订阅 =====
cmd_unsub = on_command(
    "取消订阅", rule=group_filter(), priority=5, block=True,
    permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN
)


@cmd_unsub.handle()
async def handle_unsub(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_unsub.finish("请输入要取消的订阅名称，如：取消订阅 奇遇")

    if name == "八卦":
        name = "818"

    success = await db.remove_subscribe(event.group_id, name)
    if success:
        await cmd_unsub.finish(f"✅ 已取消订阅【{name}】")
    else:
        await cmd_unsub.finish(f"⚠️ 未找到订阅【{name}】")
