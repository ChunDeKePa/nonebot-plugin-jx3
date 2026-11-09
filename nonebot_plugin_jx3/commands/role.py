"""commands/role.py — 角色信息/名片/百战指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter, vip_filter
from ..api_client import api_client, JX3APIError
from ..render import renderer
from ..database import db


async def _get_server(event):
    """获取群绑定服务器"""
    if hasattr(event, "group_id"):
        server = await db.get_server(event.group_id)
        if server:
            return server
    from ..config import plugin_config
    return plugin_config.jx3_default_server or None


# ===== 角色 =====
cmd_role = on_command("角色", rule=vip_filter(), priority=5, block=True)


@cmd_role.handle()
async def handle_role(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_role.finish("请输入角色名，如：角色 赤瞳竹")

    server = await _get_server(event)
    if not server:
        await cmd_role.finish("请先绑定服务器")

    try:
        data = await api_client.role_detail(server=server, name=name)
    except JX3APIError as e:
        await cmd_role.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("role.html", title=f"📋 角色 · {name}", data=data, server=server)
    await cmd_role.finish(MessageSegment.image(img))


# ===== 名片 =====
cmd_card = on_command("名片", rule=vip_filter(), priority=5, block=True)


@cmd_card.handle()
async def handle_card(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_card.finish("请输入角色名，如：名片 赤瞳竹")

    server = await _get_server(event)
    if not server:
        await cmd_card.finish("请先绑定服务器")

    try:
        data = await api_client.card_record(server=server, name=name)
    except JX3APIError as e:
        await cmd_card.finish(f"❌ 查询失败：{e.msg}")

    # 名片通常返回图片URL
    url = data.get("url", data.get("image", ""))
    if url:
        await cmd_card.finish(MessageSegment.image(url))
    else:
        img = await renderer.render("card.html", title=f"🃏 名片 · {name}", data=data)
        await cmd_card.finish(MessageSegment.image(img))


# ===== 所有名片 =====
cmd_cards = on_command("所有名片", rule=vip_filter(), priority=5, block=True)


@cmd_cards.handle()
async def handle_cards(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_cards.finish("请输入角色名，如：所有名片 赤瞳竹")

    server = await _get_server(event)
    if not server:
        await cmd_cards.finish("请先绑定服务器")

    try:
        data = await api_client.card_records(server=server, name=name)
    except JX3APIError as e:
        await cmd_cards.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🃏 所有名片 · {name}", data=data)
    await cmd_cards.finish(MessageSegment.image(img))


# ===== 缓存名片 =====
cmd_card_cached = on_command("缓存名片", rule=vip_filter(), priority=5, block=True)


@cmd_card_cached.handle()
async def handle_card_cached(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_card_cached.finish("请输入角色名，如：缓存名片 赤瞳竹")

    server = await _get_server(event)
    if not server:
        await cmd_card_cached.finish("请先绑定服务器")

    try:
        data = await api_client.card_cached(server=server, name=name)
    except JX3APIError as e:
        await cmd_card_cached.finish(f"❌ 查询失败：{e.msg}")

    url = data.get("url", data.get("image", ""))
    if url:
        await cmd_card_cached.finish(MessageSegment.image(url))
    else:
        img = await renderer.render("card.html", title=f"🃏 缓存名片 · {name}", data=data)
        await cmd_card_cached.finish(MessageSegment.image(img))


# ===== 角色百战 =====
cmd_role_monster = on_command("角色百战", rule=vip_filter(), priority=5, block=True)


@cmd_role_monster.handle()
async def handle_role_monster(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_role_monster.finish("请输入角色名，如：角色百战 赤瞳竹")

    server = await _get_server(event)
    if not server:
        await cmd_role_monster.finish("请先绑定服务器")

    try:
        data = await api_client.role_monster(server=server, name=name)
    except JX3APIError as e:
        await cmd_role_monster.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"⚔️ 百战 · {name}", data=data)
    await cmd_role_monster.finish(MessageSegment.image(img))


async def _parse_server_and_name(event: GroupMessageEvent, args: Message):
    """解析服务器和角色名（支持：'角色名' 或 '服务器 角色名'）"""
    text = args.extract_plain_text().strip()
    parts = text.split()
    if not parts:
        return None, ""
    if len(parts) >= 2:
        return parts[0], parts[1]
    server = await _get_server(event)
    return server, parts[0]


# ===== 面板 / 装备属性 =====
cmd_attribute = on_command("面板", aliases={"装备属性", "属性"}, rule=vip_filter(), priority=5, block=True)


@cmd_attribute.handle()
async def handle_attribute(event: GroupMessageEvent, args: Message = CommandArg()):
    server, name = await _parse_server_and_name(event, args)
    if not name:
        await cmd_attribute.finish("请输入角色名，如：面板 赤瞳竹 或 面板 梦江南 赤瞳竹")
    if not server:
        await cmd_attribute.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.calcd_attribute(server=server, name=name)
    except JX3APIError as e:
        await cmd_attribute.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🛡️ 装备属性 · {name}", data=data)
    await cmd_attribute.finish(MessageSegment.image(img))


# ===== 装备详情 =====
cmd_calcd_detail = on_command("装备详情", rule=vip_filter(), priority=5, block=True)


@cmd_calcd_detail.handle()
async def handle_calcd_detail(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    parts = text.split()
    if len(parts) < 3:
        await cmd_calcd_detail.finish("请输入角色名、心法及类型，如：装备详情 赤瞳竹 问水诀 装备")

    default_server = await _get_server(event)
    if len(parts) == 3:
        server = default_server
        name, kungfu, type_ = parts[0], parts[1], parts[2]
    else:
        server, name, kungfu, type_ = parts[0], parts[1], parts[2], parts[3]

    if not server:
        await cmd_calcd_detail.finish("请先绑定服务器或在最前指定服务器名")

    try:
        data = await api_client.calcd_detail(server=server, name=name, kungfu=kungfu, type=type_)
    except JX3APIError as e:
        await cmd_calcd_detail.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🛡️ 装备详情 · {name}", data=data)
    await cmd_calcd_detail.finish(MessageSegment.image(img))


# ===== 装备记录 =====
cmd_calcd_records = on_command("装备记录", aliases={"历史配装"}, rule=vip_filter(), priority=5, block=True)


@cmd_calcd_records.handle()
async def handle_calcd_records(event: GroupMessageEvent, args: Message = CommandArg()):
    server, name = await _parse_server_and_name(event, args)
    if not name:
        await cmd_calcd_records.finish("请输入角色名，如：装备记录 赤瞳竹")
    if not server:
        await cmd_calcd_records.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.calcd_records(server=server, name=name)
    except JX3APIError as e:
        await cmd_calcd_records.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🛡️ 历史装备快照 · {name}", data=data)
    await cmd_calcd_records.finish(MessageSegment.image(img))


# ===== 查成就 =====
cmd_achievement = on_command("查成就", aliases={"成就"}, rule=vip_filter(), priority=5, block=True)


@cmd_achievement.handle()
async def handle_achievement(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    parts = text.split()
    if len(parts) < 2:
        await cmd_achievement.finish("请输入角色名与成就名，如：查成就 赤瞳竹 侠者成双")

    default_server = await _get_server(event)
    if len(parts) == 2:
        server = default_server
        role, achieve_name = parts[0], parts[1]
    else:
        server, role, achieve_name = parts[0], parts[1], parts[2]

    if not server:
        await cmd_achievement.finish("请先绑定服务器或在最前指定服务器名")

    try:
        data = await api_client.role_achievement(server=server, role=role, name=achieve_name)
    except JX3APIError as e:
        await cmd_achievement.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🏅 成就查询 · {achieve_name}", data=data)
    await cmd_achievement.finish(MessageSegment.image(img))


# ===== 资历分布 =====
cmd_tuilan_achieve = on_command("资历分布", aliases={"成就分布"}, rule=vip_filter(), priority=5, block=True)


@cmd_tuilan_achieve.handle()
async def handle_tuilan_achieve(event: GroupMessageEvent, args: Message = CommandArg()):
    server, name = await _parse_server_and_name(event, args)
    if not name:
        await cmd_tuilan_achieve.finish("请输入角色名，如：资历分布 赤瞳竹")
    if not server:
        await cmd_tuilan_achieve.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.tuilan_achievement(server=server, name=name)
    except JX3APIError as e:
        await cmd_tuilan_achieve.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"📊 资历分布 · {name}", data=data)
    await cmd_tuilan_achieve.finish(MessageSegment.image(img))


# ===== 随机名片 =====
cmd_card_random = on_command("随机名片", rule=vip_filter(), priority=5, block=True)


@cmd_card_random.handle()
async def handle_card_random(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    parts = text.split()
    force = parts[0] if len(parts) >= 1 else None
    body = parts[1] if len(parts) >= 2 else None

    try:
        data = await api_client.card_random(force=force, body=body)
    except JX3APIError as e:
        await cmd_card_random.finish(f"❌ 获取失败：{e.msg}")

    url = data.get("url", data.get("image", ""))
    if url:
        await cmd_card_random.finish(MessageSegment.image(url))
    else:
        img = await renderer.render("card.html", title="🃏 随机名片", data=data)
        await cmd_card_random.finish(MessageSegment.image(img))


# ===== 名片预设 =====
cmd_card_preset = on_command("名片预设", rule=vip_filter(), priority=5, block=True)


@cmd_card_preset.handle()
async def handle_card_preset(event: GroupMessageEvent, args: Message = CommandArg()):
    server, name = await _parse_server_and_name(event, args)
    if not name:
        await cmd_card_preset.finish("请输入角色名，如：名片预设 赤瞳竹")
    if not server:
        await cmd_card_preset.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.card_preset(server=server, name=name)
    except JX3APIError as e:
        await cmd_card_preset.finish(f"❌ 查询失败：{e.msg}")

    url = data.get("url", data.get("image", ""))
    if url:
        await cmd_card_preset.finish(MessageSegment.image(url))
    else:
        img = await renderer.render("card.html", title=f"🃏 名片预设 · {name}", data=data)
        await cmd_card_preset.finish(MessageSegment.image(img))


# ===== 查发言 =====
cmd_chat = on_command("查发言", aliases={"聊天记录", "发言记录"}, rule=vip_filter(), priority=5, block=True)


@cmd_chat.handle()
async def handle_chat(event: GroupMessageEvent, args: Message = CommandArg()):
    server, name = await _parse_server_and_name(event, args)
    if not name:
        await cmd_chat.finish("请输入角色名，如：查发言 赤瞳竹")
    if not server:
        await cmd_chat.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.chat_records(server=server, name=name)
    except JX3APIError as e:
        await cmd_chat.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"💬 聊天记录 · {name}", data=data)
    await cmd_chat.finish(MessageSegment.image(img))
