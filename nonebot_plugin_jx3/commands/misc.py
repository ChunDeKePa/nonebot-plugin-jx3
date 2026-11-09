"""commands/misc.py — 骚话/舔狗/八卦/语音/骗子指令"""
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from ..utils import group_filter, vip_filter
from ..api_client import api_client, JX3APIError


# ===== 骚话 =====
cmd_saohua = on_command("骚话", rule=group_filter(), priority=5, block=True)


@cmd_saohua.handle()
async def handle_saohua(event: GroupMessageEvent, args: Message = CommandArg()):
    try:
        data = await api_client.saohua_random()
    except JX3APIError as e:
        await cmd_saohua.finish(f"❌ 获取失败：{e.msg}")

    await cmd_saohua.finish(data.get("text", "暂无骚话"))


# ===== 舔狗 =====
cmd_tiangou = on_command("舔狗", rule=group_filter(), priority=5, block=True)


@cmd_tiangou.handle()
async def handle_tiangou(event: GroupMessageEvent, args: Message = CommandArg()):
    try:
        data = await api_client.saohua_content()
    except JX3APIError as e:
        await cmd_tiangou.finish(f"❌ 获取失败：{e.msg}")

    await cmd_tiangou.finish(data.get("text", "暂无日记"))


# ===== 八卦 =====
cmd_bagua = on_command("八卦", rule=vip_filter(), priority=5, block=True)


@cmd_bagua.handle()
async def handle_bagua(event: GroupMessageEvent, args: Message = CommandArg()):
    tags = args.extract_plain_text().strip() or "818"
    try:
        data = await api_client.tieba_random(tags=tags)
    except JX3APIError as e:
        await cmd_bagua.finish(f"❌ 获取失败：{e.msg}")

    title = data.get("title", "")
    url = data.get("url", "")
    server = data.get("server", "")
    cls = data.get("class", "")

    msg = f"📢 {title}"
    if server and server != "-":
        msg += f"\n🌐 服务器：{server}"
    if cls:
        msg += f"\n📁 分类：{cls}"
    if url:
        msg += f"\n🔗 {url}"

    await cmd_bagua.finish(msg)

# ===== 吃什么 =====
cmd_eat = on_command("吃什么", aliases={"今天吃什么", "中午吃什么", "晚上吃什么"}, rule=group_filter(), priority=5, block=True)


@cmd_eat.handle()
async def handle_eat():
    try:
        data = await api_client.saohua_eat()
    except JX3APIError as e:
        await cmd_eat.finish(f"❌ 获取失败：{e.msg}")

    items = data if isinstance(data, list) else [str(data)]
    items_str = "、".join(f"【{x}】" for x in items)
    await cmd_eat.finish(f"🍴 侠士今天可以吃：\n{items_str}")


# ===== 喝什么 =====
cmd_drink = on_command("喝什么", aliases={"今天喝什么", "下午茶"}, rule=group_filter(), priority=5, block=True)


@cmd_drink.handle()
async def handle_drink():
    try:
        data = await api_client.saohua_drink()
    except JX3APIError as e:
        await cmd_drink.finish(f"❌ 获取失败：{e.msg}")

    items = data if isinstance(data, list) else [str(data)]
    items_str = "、".join(f"【{x}】" for x in items)
    await cmd_drink.finish(f"🥤 今日饮品推荐：\n{items_str}")


# ===== 答案之书 =====
cmd_answer = on_command("答案之书", aliases={"翻看答案", "求签"}, rule=group_filter(), priority=5, block=True)


@cmd_answer.handle()
async def handle_answer(args: Message = CommandArg()):
    q = args.extract_plain_text().strip()
    try:
        data = await api_client.saohua_answer()
    except JX3APIError as e:
        await cmd_answer.finish(f"❌ 获取失败：{e.msg}")

    ans = data.get("answer", "顺其自然")
    hearten = data.get("hearten", "")
    prefix = f"❓ 所问之事：{q}\n" if q else ""
    await cmd_answer.finish(f"📖 《答案之书》\n{prefix}「{ans}」\n\n✨ {hearten}")


# ===== 渣男语录 =====
cmd_zhanan = on_command("渣男", aliases={"渣男语录"}, rule=group_filter(), priority=5, block=True)


@cmd_zhanan.handle()
async def handle_zhanan():
    try:
        data = await api_client.saohua_zhanan()
    except JX3APIError as e:
        await cmd_zhanan.finish(f"❌ 获取失败：{e.msg}")

    await cmd_zhanan.finish(f"💔 {data.get('text', '暂无语录')}")


# ===== 分类语录 =====
cmd_context = on_command("语录", aliases={"分类语录", "疯四", "疯狂星期四", "彩虹屁", "毒鸡汤"}, rule=vip_filter(), priority=5, block=True)


@cmd_context.handle()
async def handle_context(event: GroupMessageEvent, args: Message = CommandArg()):
    plain = args.extract_plain_text().strip()
    raw = event.get_plaintext().strip()
    name = plain or ("疯狂星期四" if "疯" in raw else "彩虹屁" if "彩虹" in raw else "毒鸡汤" if "毒" in raw else "疯狂星期四")
    try:
        data = await api_client.saohua_context(name=name)
    except JX3APIError as e:
        await cmd_context.finish(f"❌ 获取失败：{e.msg}")

    await cmd_context.finish(f"📜 [{name}]\n{data.get('text', '暂无内容')}")


# ===== 骗子 =====
cmd_fraud = on_command("骗子", rule=vip_filter(), priority=5, block=True)


@cmd_fraud.handle()
async def handle_fraud(event: GroupMessageEvent, args: Message = CommandArg()):
    qq = args.extract_plain_text().strip()
    if not qq:
        await cmd_fraud.finish("请输入 QQ 号，如：骗子 123456")

    try:
        uin = int(qq)
    except ValueError:
        await cmd_fraud.finish("❌ 请输入正确的 QQ 号")

    try:
        data = await api_client.fraud_detail(uin=uin)
    except JX3APIError as e:
        if e.code == 404:
            await cmd_fraud.finish(f"✅ QQ {uin} 未在骗子库中记录")
        await cmd_fraud.finish(f"❌ 查询失败：{e.msg}")

    # 有记录
    records = data if isinstance(data, list) else [data]
    lines = [f"⚠️ QQ {uin} 骗子记录："]
    for r in records:
        server = r.get("server", "")
        detail = r.get("detail", r.get("content", ""))
        lines.append(f"  🌐 {server}：{detail}")

    await cmd_fraud.finish("\n".join(lines))
