"""commands/rank.py — 榜单/试炼排行/掉落统计指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter, get_server, vip_filter
from ..api_client import api_client, JX3APIError
from ..render import renderer


# ===== 榜单 =====
cmd_rank = on_command("榜单", rule=vip_filter(), priority=5, block=True)


@cmd_rank.handle()
async def handle_rank(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await cmd_rank.finish("请输入榜单类型，如：榜单 个人")

    server = await get_server(event, args)
    if not server:
        await cmd_rank.finish("请先绑定服务器")

    try:
        data = await api_client.rank_statistical(server=server, type=text)
    except JX3APIError as e:
        await cmd_rank.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 {text}榜单",
        data=data,
        cache_key=f"rank:{server}:{text}",
        cache_ttl=1800,
    )
    await cmd_rank.finish(MessageSegment.image(img))


# ===== 试炼排行 =====
cmd_trials = on_command("试炼排行", rule=vip_filter(), priority=5, block=True)


@cmd_trials.handle()
async def handle_trials(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()

    server = await get_server(event, args)
    if not server:
        await cmd_trials.finish("请先绑定服务器")

    school = text if text else ""

    try:
        data = await api_client.rank_trials(server=server, school=school)
    except JX3APIError as e:
        await cmd_trials.finish(f"❌ 查询失败：{e.msg}")

    # 剥离外层包装
    if isinstance(data, dict):
        data = data.get("data", [])

    title = f"🗡️ 试炼排行" + (f" · {school}" if school else "")
    img = await renderer.render(
        "table.html",
        title=title,
        data=data,
        columns=["role_name", "max_level", "total_score", "equip_score"],
        headers=["角色名", "最高层数", "试炼分数", "装备分数"],
        cache_key=f"trials:{server}:{school}",
        cache_ttl=1800,
    )
    await cmd_trials.finish(MessageSegment.image(img))


# ===== 掉落 =====
cmd_reward = on_command("掉落", rule=vip_filter(), priority=5, block=True)


@cmd_reward.handle()
async def handle_reward(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_reward.finish("请输入副本名称，如：掉落 敖龙岛")

    server = await get_server(event, args)
    if not server:
        await cmd_reward.finish("请先绑定服务器")

    try:
        data = await api_client.reward_statistics(server=server, name=name)
    except JX3APIError as e:
        await cmd_reward.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🎁 掉落统计 · {name}",
        data=data,
        cache_key=f"reward:{server}:{name}",
        cache_ttl=1800,
    )
    await cmd_reward.finish(MessageSegment.image(img))


# ===== 名剑总榜 =====
cmd_rank_arena = on_command("名剑总榜", aliases={"跨服名剑", "名剑全服榜"}, rule=vip_filter(), priority=5, block=True)


@cmd_rank_arena.handle()
async def handle_rank_arena(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    mode = 22 if "2" in text else (55 if "5" in text else 33)

    try:
        data = await api_client.rank_arena(mode=mode)
    except JX3APIError as e:
        await cmd_rank_arena.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 名剑大会全服总榜 ({mode}v{mode})",
        data=data,
        cache_key=f"rank_arena:{mode}",
        cache_ttl=1800,
    )
    await cmd_rank_arena.finish(MessageSegment.image(img))


# ===== 争霸榜 =====
cmd_rank_champ = on_command("争霸榜", aliases={"武林争霸", "争霸赛"}, rule=vip_filter(), priority=5, block=True)


@cmd_rank_champ.handle()
async def handle_rank_champ(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    camp = 2 if "恶" in text else 1
    camp_str = "恶人谷" if camp == 2 else "浩气盟"

    try:
        data = await api_client.rank_championship(camp=camp)
    except JX3APIError as e:
        await cmd_rank_champ.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 帮会武林争霸赛排行 ({camp_str})",
        data=data,
        cache_key=f"rank_champ:{camp}",
        cache_ttl=1800,
    )
    await cmd_rank_champ.finish(MessageSegment.image(img))


# ===== 捕快榜 =====
cmd_rank_constable = on_command("捕快榜", rule=vip_filter(), priority=5, block=True)


@cmd_rank_constable.handle()
async def handle_rank_constable(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_rank_constable.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.rank_constable(server=server)
    except JX3APIError as e:
        await cmd_rank_constable.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 捕快榜 · {server}",
        data=data,
        cache_key=f"rank_constable:{server}",
        cache_ttl=1800,
    )
    await cmd_rank_constable.finish(MessageSegment.image(img))


# ===== 浪客榜 =====
cmd_rank_outlaw = on_command("浪客榜", rule=vip_filter(), priority=5, block=True)


@cmd_rank_outlaw.handle()
async def handle_rank_outlaw(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_rank_outlaw.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.rank_outlaw(server=server)
    except JX3APIError as e:
        await cmd_rank_outlaw.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 浪客榜 · {server}",
        data=data,
        cache_key=f"rank_outlaw:{server}",
        cache_ttl=1800,
    )
    await cmd_rank_outlaw.finish(MessageSegment.image(img))


# ===== 决斗榜 =====
cmd_rank_wanted = on_command("决斗榜", aliases={"赏金榜"}, rule=vip_filter(), priority=5, block=True)


@cmd_rank_wanted.handle()
async def handle_rank_wanted(event: GroupMessageEvent, args: Message = CommandArg()):
    server = await get_server(event, args)
    if not server:
        await cmd_rank_wanted.finish("请先绑定服务器或输入服务器名")

    try:
        data = await api_client.rank_wanted(server=server)
    except JX3APIError as e:
        await cmd_rank_wanted.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🏆 决斗赏金榜 · {server}",
        data=data,
        cache_key=f"rank_wanted:{server}",
        cache_ttl=1800,
    )
    await cmd_rank_wanted.finish(MessageSegment.image(img))


# ===== 排行统计 =====
cmd_rank_stats = on_command("排行统计", rule=vip_filter(), priority=5, block=True)


@cmd_rank_stats.handle()
async def handle_rank_stats(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    server = await get_server(event, args)

    try:
        data = await api_client.rank_statistics(server=server or "", name=text)
    except JX3APIError as e:
        await cmd_rank_stats.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"📊 排行统计 · {server}",
        data=data,
        cache_key=f"rank_stats:{server}:{text}",
        cache_ttl=1800,
    )
    await cmd_rank_stats.finish(MessageSegment.image(img))


# ===== 试炼秒伤 =====
cmd_trial_boss = on_command("试炼秒伤", rule=vip_filter(), priority=5, block=True)


@cmd_trial_boss.handle()
async def handle_trial_boss(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    parts = text.split()
    if len(parts) < 2:
        await cmd_trial_boss.finish("请输入赛季与层数，如：试炼秒伤 奉天证道 100")

    season, floor_str = parts[0], parts[1]
    try:
        floor = int(floor_str)
    except ValueError:
        await cmd_trial_boss.finish("❌ 层数必须为纯数字")

    try:
        data = await api_client.trial_bosses(season=season, floor=floor)
    except JX3APIError as e:
        await cmd_trial_boss.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title=f"🗡️ 试炼秒伤 · {season} 第{floor}层",
        data=data,
        cache_key=f"trial_boss:{season}:{floor}",
        cache_ttl=3600,
    )
    await cmd_trial_boss.finish(MessageSegment.image(img))


# ===== 试炼赛季 =====
cmd_trial_season = on_command("试炼赛季", rule=vip_filter(), priority=5, block=True)


@cmd_trial_season.handle()
async def handle_trial_season(event: GroupMessageEvent):
    try:
        data = await api_client.trial_seasons()
    except JX3APIError as e:
        await cmd_trial_season.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html",
        title="🗡️ 试炼之地历史赛季",
        data=data,
        cache_key="trial_seasons",
        cache_ttl=86400,
    )
    await cmd_trial_season.finish(MessageSegment.image(img))
