"""commands/steed.py — 的卢/赤兔/马场指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter, get_server, vip_filter
from ..api_client import api_client, JX3APIError
from ..render import renderer, get_game_day_str, get_game_day_ttl, get_weekly_ttl


# ===== 的卢 =====
cmd_steed = on_command("的卢", rule=vip_filter(), priority=5, block=True)


@cmd_steed.handle()
async def handle_steed(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_steed.finish("请先绑定服务器")

    try:
        data = await api_client.steed_records(server=server)
    except JX3APIError as e:
        await cmd_steed.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🐎 的卢记录 · {server}", data=data)
    await cmd_steed.finish(MessageSegment.image(img))


# ===== 赤兔 =====
cmd_chitu = on_command("赤兔", rule=vip_filter(), priority=5, block=True)


@cmd_chitu.handle()
async def handle_chitu(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_chitu.finish("请先绑定服务器")

    day_str = get_game_day_str()
    ttl = get_game_day_ttl()

    try:
        data = await api_client.chitu_records(server=server)
    except JX3APIError as e:
        await cmd_chitu.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html", 
        cache_key=f"chitu:{server}:{day_str}",
        cache_ttl=ttl, # 每天07:00刷新
        title=f"🐴 赤兔记录 · {server}", 
        data=data
    )
    await cmd_chitu.finish(MessageSegment.image(img))


# ===== 赤兔周报 =====
cmd_chitu_week = on_command("赤兔周报", rule=vip_filter(), priority=5, block=True)


@cmd_chitu_week.handle()
async def handle_chitu_week(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_chitu_week.finish("请先绑定服务器")

    day_str = get_game_day_str()
    ttl = get_weekly_ttl(target_weekday=1) # 每周二07:00刷新

    try:
        data = await api_client.chitu_week_records(server=server)
    except JX3APIError as e:
        await cmd_chitu_week.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html", 
        cache_key=f"chitu_week:{server}:{day_str}",
        cache_ttl=ttl,
        title=f"🐴 赤兔周报 · {server}", 
        data=data
    )
    await cmd_chitu_week.finish(MessageSegment.image(img))


# ===== 马场 =====
cmd_ranch = on_command("马场", rule=vip_filter(), priority=5, block=True)


@cmd_ranch.handle()
async def handle_ranch(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_ranch.finish("请先绑定服务器")

    try:
        data = await api_client.ranch_records(server=server)
    except JX3APIError as e:
        await cmd_ranch.finish(f"❌ 查询失败：{e.msg}")

    formatted_data = []
    note_text = ""
    if isinstance(data, dict):
        raw_map = data.get("data", {})
        note_text = data.get("note", "")
        if isinstance(raw_map, dict):
            for map_name, status_list in raw_map.items():
                status_str = status_list[0] if status_list else ""
                formatted_data.append({"map_name": map_name, "status": status_str})
        elif isinstance(raw_map, str) and " / " in raw_map:
            maps_str, status_str = raw_map.split(" / ", 1)
            for m in maps_str.split("、"):
                formatted_data.append({"map_name": m.strip(), "status": status_str.strip()})

    img = await renderer.render(
        "table.html",
        title=f"🏇 马场刷新 · {server}",
        data=formatted_data,
        columns=["map_name", "status"],
        headers=["刷新地图", "马匹状态"],
        note=note_text,
    )
    await cmd_ranch.finish(MessageSegment.image(img))


# ===== 抓马播报 =====
cmd_ranch_chat = on_command("抓马倒计时", aliases={"抓马播报", "马场通告"}, rule=vip_filter(), priority=5, block=True)


@cmd_ranch_chat.handle()
async def handle_ranch_chat(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_ranch_chat.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.ranch_chat(server=server)
    except JX3APIError as e:
        await cmd_ranch_chat.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render("table.html", title=f"🏇 抓马播报 · {server}", data=data)
    await cmd_ranch_chat.finish(MessageSegment.image(img))
