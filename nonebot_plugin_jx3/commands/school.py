"""commands/school.py — 小药/技改/阵眼/奇穴/技能/资历指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter, get_server, vip_filter
from ..api_client import api_client, JX3APIError
from ..render import renderer


# ===== 小药 =====
cmd_foods = on_command("小药", aliases={"小药推荐", "小吃小药", "小药清单"}, rule=group_filter(), priority=5, block=True)


@cmd_foods.handle()
async def handle_foods(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_foods.finish("请输入心法名称，如：小药 花间游")

    try:
        data = await api_client.school_foods(name=name)
    except JX3APIError as e:
        await cmd_foods.finish(f"❌ 查询失败：{e.msg}")

    # 小药字段不展示列标题 (headers)，直接呈现内容列表
    img = await renderer.render(
        "table.html", 
        cache_key=f"foods:{name}",
        cache_ttl=86400, # 24小时心法小药缓存
        title=f"💊 小药推荐 · {name}", 
        data=data,
        columns=["class", "name", "boost"]
    )
    await cmd_foods.finish(MessageSegment.image(img))


# ===== 技改 =====
cmd_rework = on_command("技改", rule=group_filter(), priority=5, block=True)


@cmd_rework.handle()
async def handle_rework(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    try:
        data = await api_client.skill_rework(name=name)
    except JX3APIError as e:
        await cmd_rework.finish(f"❌ 查询失败：{e.msg}")

    if not data:
        await cmd_rework.finish(f"未找到相关技改记录" + (f"（关键词：{name}）" if name else ""))

    # 包含官方链接，采用文本消息发送以支持在聊天界面直接点击跳转
    msg_lines = ["🔧 【剑网3 官方武学调整（技改）】"]
    for idx, item in enumerate(data[:6], 1):
        title = item.get("title", "")
        url = item.get("url", "")
        time_str = item.get("time", "")
        line = f"{idx}. {title}"
        if time_str:
            line += f"\n   📅 时间：{time_str}"
        if url:
            line += f"\n   🔗 {url}"
        msg_lines.append(line)

    await cmd_rework.finish("\n\n".join(msg_lines))


# ===== 阵眼 =====
cmd_matrix = on_command("阵眼", rule=vip_filter(), priority=5, block=True)


@cmd_matrix.handle()
async def handle_matrix(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_matrix.finish("请输入心法名称，如：阵眼 花间游")

    try:
        data = await api_client.school_matrix(name=name)
    except JX3APIError as e:
        await cmd_matrix.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "matrix.html", 
        cache_key=f"matrix:{name}",
        cache_ttl=86400, # 24小时心法阵眼缓存
        title=f"👁️ 阵眼 · {name}", 
        data=data
    )
    await cmd_matrix.finish(MessageSegment.image(img))


# ===== 奇穴 =====
cmd_talent = on_command("奇穴", rule=vip_filter(), priority=5, block=True)


@cmd_talent.handle()
async def handle_talent(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_talent.finish("请输入心法名称，如：奇穴 花间游")

    try:
        data = await api_client.school_talent(name=name)
    except JX3APIError as e:
        await cmd_talent.finish(f"❌ 查询失败：{e.msg}")

    # ===== 扁平化深层奇穴嵌套结构 =====
    formatted_list = []
    for tier in data:
        level_num = tier.get("level", "")
        talents_arr = tier.get("data", [])
        talents_str = "、".join([x.get("name", "") for x in talents_arr])
        formatted_list.append({
            "level": f"第{level_num}重",
            "talents": talents_str
        })
    # ==================================

    img = await renderer.render(
        "table.html", 
        cache_key=f"talent:{name}",
        cache_ttl=86400, # 24小时奇穴缓存
        title=f"⭐ 奇穴 · {name}", 
        data=formatted_list,
        columns=["level", "talents"],
        headers=["重数", "奇穴选择"]
    )
    await cmd_talent.finish(MessageSegment.image(img))


# ===== 技能 =====
cmd_skills = on_command("技能", rule=vip_filter(), priority=5, block=True)


@cmd_skills.handle()
async def handle_skills(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_skills.finish("请输入心法名称，如：技能 花间游")

    try:
        data = await api_client.school_skills(name=name)
    except JX3APIError as e:
        await cmd_skills.finish(f"❌ 查询失败：{e.msg}")
        
    # ===== 解析深层多维技能封装为扁平结构 =====
    formatted_list = []
    if isinstance(data, list):
        for item in data:
            category = item.get("class", "")
            skill_list = item.get("data", [])
            for skill in skill_list:
                formatted_list.append({
                    "category": category,
                    "name": skill.get("name", ""),
                    "interval": skill.get("interval", ""),
                    "simpleDesc": skill.get("simpleDesc", "")
                })
    # ==========================================

    img = await renderer.render(
        "table.html", 
        cache_key=f"skills:{name}",
        cache_ttl=86400, # 24小时心法技能缓存
        title=f"⚡ 技能 · {name}", 
        data=formatted_list,
        columns=["category", "name", "interval", "simpleDesc"],
        headers=["武学分类", "技能名称", "调息状态", "核心描述"]
    )
    await cmd_skills.finish(MessageSegment.image(img))


# ===== 资历 =====
cmd_seniority = on_command("资历", rule=vip_filter(), priority=5, block=True)


@cmd_seniority.handle()
async def handle_seniority(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()

    server = await get_server(event, args)
    if not server:
        await cmd_seniority.finish("请先绑定服务器或输入服务器名")

    # 解析可选的心法参数
    parts = text.split(maxsplit=1)
    school = parts[1] if len(parts) > 1 else ""

    try:
        data = await api_client.school_seniority(server=server, school=school)
    except JX3APIError as e:
        await cmd_seniority.finish(f"❌ 查询失败：{e.msg}")

    title = f"📊 资历排行" + (f" · {school}" if school else "")
    img = await renderer.render("table.html", title=title, data=data)
    await cmd_seniority.finish(MessageSegment.image(img))


# ===== 急速 =====
cmd_haste = on_command("急速", aliases={"急速计算", "阈值"}, rule=vip_filter(), priority=5, block=True)


@cmd_haste.handle()
async def handle_haste(event: GroupMessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    cd = 1.5
    if text:
        try:
            cd = float(text)
        except ValueError:
            pass

    try:
        data = await api_client.skill_calculate(cooldown=cd)
    except JX3APIError as e:
        await cmd_haste.finish(f"❌ 计算失败：{e.msg}")

    img = await renderer.render(
        "table.html", 
        cache_key=f"haste:{cd}",
        cache_ttl=None, # 数学常数，重启不变
        title=f"⚡ 急速阈值计算 (CD: {cd}s)", 
        data=data
    )
    await cmd_haste.finish(MessageSegment.image(img))


# ===== 配装 =====
cmd_school_search = on_command("配装", aliases={"配装推荐"}, rule=vip_filter(), priority=5, block=True)


@cmd_school_search.handle()
async def handle_school_search(event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await cmd_school_search.finish("请输入心法名称，如：配装 花间游")

    try:
        data = await api_client.school_search(name=name)
    except JX3APIError as e:
        await cmd_school_search.finish(f"❌ 查询失败：{e.msg}")

    img = await renderer.render(
        "table.html", 
        cache_key=f"school_search:{name}",
        cache_ttl=86400, # 24小时配装方案缓存
        title=f"🥋 配装推荐 · {name}", 
        data=data
    )
    await cmd_school_search.finish(MessageSegment.image(img))

