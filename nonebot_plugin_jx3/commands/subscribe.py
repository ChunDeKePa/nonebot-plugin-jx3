"""commands/subscribe.py — 订阅管理指令（支持独立图文渲染面板）"""
from nonebot import on_command, get_driver
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter
from ..database import db
from ..render import renderer


# ===== 订阅 =====
cmd_subscribe = on_command(
    "订阅", 
    aliases={"订阅列表", "订阅帮助", "推送列表", "推送"}, 
    rule=group_filter(), 
    priority=5, 
    block=True
)


@cmd_subscribe.handle()
async def handle_subscribe(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()

    if not name:
        # 无参数：独立绘制订阅与推送管理高清图（群状态缓存）
        server = await db.get_server(event.group_id)
        current = await db.get_subscribes(event.group_id)
        sub_tuple = tuple(sorted(current))
        img = await renderer.render(
            "subscribe.html",
            cache_key=f"subscribe:{event.group_id}:{server}:{sub_tuple}",
            cache_ttl=86400, # 状态未变更前常驻缓存
            server=server or "未绑定",
            group_id=event.group_id,
            current=current,
        )
        await cmd_subscribe.finish(MessageSegment.image(img))

    # 权限校验：仅群主、管理员或超级管理员可修改订阅
    superusers = get_driver().config.superusers
    is_admin = str(event.user_id) in superusers or event.sender.role in ("admin", "owner")
    if not is_admin:
        await cmd_subscribe.finish("⚠️ 仅群主或管理员可以修改本群订阅设置哦～")

    if name == "八卦":
        name = "818"

    # 有参数：添加订阅
    if name not in db.SUBSCRIBE_NAMES:
        await cmd_subscribe.finish(
            f"❌ 无效的订阅名称：{name}\n"
            f"📝 发送「订阅」即可查看完整可订阅事件清单图"
        )

    success = await db.add_subscribe(event.group_id, name)
    if success:
        # 订阅变更，立即使本群订阅图缓存失效
        renderer.invalidate(f"subscribe:{event.group_id}")
        await cmd_subscribe.finish(f"✅ 成功开启本群【{name}】事件推送！")
    else:
        await cmd_subscribe.finish(f"⚠️ 本群已订阅【{name}】，无需重复订阅")


# ===== 取消订阅 =====
cmd_unsub = on_command(
    "取消订阅", 
    rule=group_filter(), 
    priority=5, 
    block=True
)


@cmd_unsub.handle()
async def handle_unsub(event: GroupMessageEvent, args: Message = CommandArg()):
    superusers = get_driver().config.superusers
    is_admin = str(event.user_id) in superusers or event.sender.role in ("admin", "owner")
    if not is_admin:
        await cmd_unsub.finish("⚠️ 仅群主或管理员可以取消本群订阅设置哦～")

    name = args.extract_plain_text().strip()
    if not name:
        await cmd_unsub.finish("请输入要取消的订阅名称，如：取消订阅 奇遇")

    if name == "八卦":
        name = "818"

    success = await db.remove_subscribe(event.group_id, name)
    if success:
        # 订阅变更，立即使本群订阅图缓存失效
        renderer.invalidate(f"subscribe:{event.group_id}")
        await cmd_unsub.finish(f"✅ 已成功取消本群【{name}】事件推送")
    else:
        await cmd_unsub.finish(f"⚠️ 本群尚未订阅【{name}】")
