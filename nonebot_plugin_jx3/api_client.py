"""HTTP API 客户端 — 封装所有 JX3API 端点（适配 JX3API 最新 OpenAPI 规范与接口调用方式）"""
from typing import Any, Dict, List, Optional
import httpx
from nonebot import logger


class JX3APIError(Exception):
    """API 请求错误"""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"[{code}] {msg}")


class JX3APIClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self.base_url = "https://www.jx3api.com"
        self.token = ""
        self.ticket = ""

    def init_config(self):
        """延迟初始化配置，避免启动时循环导入"""
        from .config import plugin_config
        self.base_url = (plugin_config.jx3api_base_url or "https://www.jx3api.com").rstrip("/")
        self.token = plugin_config.jx3api_token or plugin_config.jx3api_key
        self.ticket = plugin_config.jx3_tuilan_ticket

    async def start(self):
        """启动 HTTP 客户端"""
        self.init_config()
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=15.0
        )
        logger.info("[JX3] HTTP API 客户端已启动")

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            logger.info("[JX3] HTTP API 客户端已关闭")

    async def _request(self, endpoint: str, method: str = "GET", **params) -> Any:
        """统一请求方法。
        - 根据最新 JX3API 规范，端点直接使用根路径（非 /data/ 前缀），默认采用 GET 请求
        - 自动注入 token（如果有）
        - 自动注入 ticket（如果有）
        - 自动过滤 None 及空字符串参数
        - 统一错误处理并返回 data 字段
        """
        if not self._client:
            await self.start()

        if self.token:
            params.setdefault("token", self.token)
        if self.ticket:
            params.setdefault("ticket", self.ticket)

        # 过滤 None 和空字符串参数（保留 0 和 False 等有效值）
        cleaned_params = {k: v for k, v in params.items() if v is not None and v != ""}

        try:
            if method.upper() == "POST":
                resp = await self._client.post(endpoint, json=cleaned_params)
            else:
                resp = await self._client.get(endpoint, params=cleaned_params)
            result = resp.json()
        except Exception as e:
            raise JX3APIError(0, f"请求异常：{e}")

        if not isinstance(result, dict):
            raise JX3APIError(getattr(resp, "status_code", 0), "响应数据格式异常")

        if result.get("code") != 200:
            raise JX3APIError(result.get("code", getattr(resp, "status_code", 0)), result.get("msg", "未知错误"))

        return result.get("data")

    # ============================================================
    # 1. 活动情报 (Activity Intelligence)
    # ============================================================

    async def active_calendar(self, server: str = "", num: int = 0, mode: str = "day") -> dict:
        """活动日历。单日或前后区间的日常活动推演。
        endpoint: /active/calendar
        params: num(天数偏移/区间半径, 默认0), mode('day'单日/'list'前后区间)
        """
        return await self._request("/active/calendar", num=num, mode=mode)

    async def active_list_calendar(self, num: int = 15) -> list:
        """活动月历。查询指定范围的日常活动列表。
        endpoint: /active/calendar
        params: num(区间半径, 默认15), mode='list'
        """
        res = await self._request("/active/calendar", num=num, mode="list")
        items = []
        if isinstance(res, dict) and "total" in res:
            items = res.get("total", [])
        elif isinstance(res, list):
            items = res
        # 兼容老版本代码读取 month 和 day
        for item in items:
            if isinstance(item, dict) and "date" in item and ("month" not in item or "day" not in item):
                parts = item["date"].split("-")
                if len(parts) == 3:
                    item.setdefault("month", parts[1])
                    item.setdefault("day", parts[2])
        return items

    async def active_celebs(self, name: str = "") -> Any:
        """地图活动。楚天社 / 云从社 / 披风会接下来排期。
        endpoint: /active/celebs
        params: name(事件名称，如楚天社/云从社)
        """
        return await self._request("/active/celebs", name=name)

    async def chitu_records(self, server: str = "") -> list:
        """今日赤兔。今日赤兔预告及出世记录。
        endpoint: /chitu/records
        """
        data = await self._request("/chitu/records")
        if server and isinstance(data, list):
            filtered = [item for item in data if isinstance(item, dict) and item.get("server") == server]
            return filtered if filtered else data
        return data if isinstance(data, list) else []

    async def chitu_week_records(self, server: str = "") -> list:
        """本周赤兔。本周期赤兔预告及出世记录，周二 07:00 重置。
        endpoint: /chitu/week/records
        """
        data = await self._request("/chitu/week/records")
        if server and isinstance(data, list):
            filtered = [item for item in data if isinstance(item, dict) and item.get("server") == server]
            return filtered if filtered else data
        return data if isinstance(data, list) else []

    async def ranch_records(self, server: str, expired: int = 0) -> dict:
        """马场事件。马场播报预告 + 本周期赤兔/的卢出世情况。
        endpoint: /ranch/records
        params: server, expired(是否包含已过期, 默认0)
        """
        return await self._request("/ranch/records", server=server, expired=expired)

    async def ranch_chat(self, server: str) -> dict:
        """马场预告。解析各地图下一匹马出世预计时刻。
        endpoint: /ranch/chat
        params: server
        """
        return await self._request("/ranch/chat", server=server)

    async def steed_records(self, server: str = "") -> list:
        """的卢拍卖。各服最新或指定服最新 10 条的卢拍卖记录。
        endpoint: /steed/records
        params: server(可选)
        """
        return await self._request("/steed/records", server=server)

    async def firework_records(self, server: str, name: str) -> list:
        """烟花记录。角色作为送花人或收花人的烟花记录，时间倒序。
        endpoint: /firework/records
        params: server, name(角色名)
        """
        return await self._request("/firework/records", server=server, name=name)

    async def show_records(self, server: str, name: str) -> list:
        """烟花记录别名（向后兼容）"""
        return await self.firework_records(server=server, name=name)

    # ============================================================
    # 2. 系统工具 (System Tools)
    # ============================================================

    async def exam_search(self, subject: str, limit: int = 10) -> list:
        """科举答题。按题目模糊匹配返回候选答案。
        endpoint: /exam/search
        params: subject(试题关键字), limit(返回数量, 默认10)
        """
        return await self._request("/exam/search", subject=subject, limit=limit)

    async def status_check(self, server: str = "", type: int = 1) -> Any:
        """大区状态/开服状态。查询服务器维护/在线/爆满状态。
        endpoint: /server/status/check
        params: server(可选), type(1=数据库合集, 其他=xoyo在线状态)
        """
        data = await self._request("/server/status/check", server=server, type=type)
        if server and isinstance(data, list) and len(data) > 0:
            for item in data:
                if isinstance(item, dict) and item.get("server") == server:
                    return item
            return data[0]
        return data

    async def master_search(self, name: str) -> list:
        """搜索区服。根据名称检索对应服务器信息。
        通过 /server/status/check 获取列表并进行模糊匹配。
        """
        data = await self._request("/server/status/check", type=1)
        if isinstance(data, list):
            return [
                item for item in data
                if isinstance(item, dict) and (name in item.get("server", "") or name in item.get("zone", ""))
            ]
        return data if isinstance(data, list) else []

    async def skill_rework(self, name: str = "") -> list:
        """技改记录。官方武学调整公告列表。
        endpoint: /skill/rework
        """
        data = await self._request("/skill/rework")
        if name and isinstance(data, list):
            matched = [item for item in data if isinstance(item, dict) and name in item.get("title", "")]
            return matched if matched else data
        return data if isinstance(data, list) else []

    async def skill_calculate(self, cooldown: float = 1.5) -> dict:
        """急速计算。按技能 cd 推算各急速档位读条与时长。
        endpoint: /skill/calculate
        params: cooldown
        """
        return await self._request("/skill/calculate", cooldown=cooldown)

    async def sound_converter(
        self,
        appkey: str,
        access: str,
        secret: str,
        text: str,
        voice: str = "Aitong",
        format: str = "mp3",
        sample_rate: int = 16000,
        volume: str = "50",
        speech_rate: str = "0",
        pitch_rate: str = "0",
    ) -> dict:
        """语音合成。
        endpoint: /sound/converter
        """
        return await self._request(
            "/sound/converter",
            appkey=appkey,
            access=access,
            secret=secret,
            text=text,
            voice=voice,
            format=format,
            sample_rate=sample_rate,
            volume=volume,
            speech_rate=speech_rate,
            pitch_rate=pitch_rate,
        )

    # ============================================================
    # 3. 新闻公告 (News & Announce)
    # ============================================================

    async def news_announce(self, limit: int = 5) -> list:
        """维护公告。标题含“版本更新”的维护公告列表。
        endpoint: /news/announce
        params: limit(数量, 默认5)
        """
        return await self._request("/news/announce", limit=limit)

    async def news_records(self, limit: int = 10) -> list:
        """新闻资讯。最新官方新闻资讯列表。
        endpoint: /news/records
        params: limit(数量, 默认10)
        """
        return await self._request("/news/records", limit=limit)

    async def news_allnews(self, limit: int = 10) -> list:
        """新闻资讯别名（向后兼容）"""
        return await self.news_records(limit=limit)

    # ============================================================
    # 4. 家园相关 (Home)
    # ============================================================

    async def home_flower(self, server: str, name: str = "", map: str = "") -> dict:
        """家园鲜花。鲜花行情与路线。
        endpoint: /home/flower
        params: server, name(鲜花名称, 可选), map(地图名称, 可选)
        """
        return await self._request("/home/flower", server=server, name=name, map=map)

    async def home_furniture(self, name: str) -> dict:
        """家园装饰。查询装饰图纸信息。
        endpoint: /home/furniture
        params: name(装饰名称)
        """
        return await self._request("/home/furniture", name=name)

    async def home_travel(self, name: str) -> dict:
        """器物图谱。查询器物图谱信息。
        endpoint: /home/travel
        params: name(器物名称)
        """
        return await self._request("/home/travel", name=name)

    # ============================================================
    # 5. 门派心法 (School & Martial)
    # ============================================================

    async def food_list(self, name: str = "") -> Any:
        """小吃小药。查询指定心法推荐的小吃小药。
        endpoint: /food/list
        params: name(心法名称, 可选)
        """
        return await self._request("/food/list", name=name)

    async def school_foods(self, name: str = "") -> Any:
        """小吃小药别名（向后兼容）"""
        return await self.food_list(name=name)

    async def school_matrix(self, name: str) -> dict:
        """阵眼效果。查询心法推栏阵眼效果与描述。
        endpoint: /school/matrix
        params: name(心法名称)
        """
        return await self._request("/school/matrix", name=name)

    async def school_talent(self, name: str, update: int = 0) -> list:
        """奇穴信息。查询心法奇穴招式技能。
        endpoint: /school/talent
        params: name(心法名称), update(是否更新, 默认0)
        """
        return await self._request("/school/talent", name=name, update=update)

    async def school_skills(self, name: str, update: int = 0) -> list:
        """技能信息。查询心法招式技能列表。
        endpoint: /school/skills
        params: name(心法名称), update(是否更新, 默认0)
        """
        return await self._request("/school/skills", name=name, update=update)

    async def school_seniority(self, server: str = "ALL", school: str = "ALL") -> list:
        """资历榜单。全服或指定服指定门派资历排行。
        endpoint: /school/seniority
        params: server, school
        """
        return await self._request("/school/seniority", server=server, school=school)

    async def school_search(self, name: str, mode: Optional[str] = None) -> dict:
        """配装搜索。推栏推荐配装。
        endpoint: /school/search
        params: name(门派/心法名称), mode(玩法模式, 可选)
        """
        return await self._request("/school/search", name=name, mode=mode)

    # ============================================================
    # 6. 角色与名片 (Role & Card)
    # ============================================================

    async def role_detail(self, server: str, name: str, history: int = 0) -> dict:
        """角色详情。查询角色信息，包含曾用名与历史帮会。
        endpoint: /role/detail
        params: server, name(角色名), history(0=异步采集, 1=同步采集)
        """
        return await self._request("/role/detail", server=server, name=name, history=history)

    async def role_achievement(self, server: str, role: str, name: str) -> dict:
        """成就查询。查询角色指定成就完成情况。
        endpoint: /role/achievement
        params: server, role(角色名), name(成就名)
        """
        return await self._request("/role/achievement", server=server, role=role, name=name)

    async def card_record(self, server: str, name: str) -> dict:
        """角色名片。获取角色最新名片。
        endpoint: /card/record
        params: server, name(角色名)
        """
        return await self._request("/card/record", server=server, name=name)

    async def card_records(self, server: str, name: str, like: bool = False) -> list:
        """名片历史。获取角色历史名片列表。
        endpoint: /card/records
        params: server, name(角色名), like(是否只看点赞)
        """
        return await self._request("/card/records", server=server, name=name, like=like)

    async def card_cached(self, server: str, name: str) -> dict:
        """名片缓存。取已缓存名片。
        endpoint: /card/cached
        params: server, name(角色名)
        """
        return await self._request("/card/cached", server=server, name=name)

    async def card_preset(self, server: str, name: str) -> dict:
        """名片预设。角色推栏名片预设图与获赞数。
        endpoint: /card/preset
        params: server, name(角色名)
        """
        return await self._request("/card/preset", server=server, name=name)

    async def card_random(self, server: Optional[str] = None, force: Optional[str] = None, body: Optional[str] = None) -> dict:
        """随机名片。按门派/体型随机取一张名片。
        endpoint: /card/random
        params: server, force(门派), body(体型)
        """
        return await self._request("/card/random", server=server, force=force, body=body)

    async def monster_records(self, server: str, name: str) -> dict:
        """角色百战。角色的百战技能配装与进度。
        endpoint: /monster/records
        params: server, name(角色名)
        """
        return await self._request("/monster/records", server=server, name=name)

    async def role_monster(self, server: str, name: str) -> dict:
        """角色百战别名（向后兼容）"""
        return await self.monster_records(server=server, name=name)

    async def calcd_attribute(self, server: str, name: str, format: str = "calcd") -> dict:
        """装备属性。查询角色装备与属性面板。
        endpoint: /calcd/attribute
        params: server, name, format('calcd'/'client')
        """
        return await self._request("/calcd/attribute", server=server, name=name, format=format)

    async def calcd_detail(self, server: str, name: str, kungfu: str, type: str, format: str = "calcd") -> dict:
        """装备详情。按心法与类型定位历史配装。
        endpoint: /calcd/detail
        params: server, name, kungfu, type, format('calcd'/'client')
        """
        return await self._request("/calcd/detail", server=server, name=name, kungfu=kungfu, type=type, format=format)

    async def calcd_records(self, server: str, name: str) -> list:
        """装备记录。查询角色历史装备快照【需 VIP 2 令牌】。
        endpoint: /calcd/records
        params: server, name
        """
        return await self._request("/calcd/records", server=server, name=name)

    async def chat_records(self, server: str, name: str, limit: int = 20, page: int = 1) -> list:
        """角色聊天。分页查询指定服务器角色的聊天记录【需 VIP 2 令牌】。
        endpoint: /chat/records
        params: server, name, limit(默认20), page(默认1)
        """
        return await self._request("/chat/records", server=server, name=name, limit=limit, page=page)


    # ============================================================
    # 7. 奇遇相关 (Adventure)
    # ============================================================

    async def event_records(self, server: str, name: str, full: int = 0) -> list:
        """奇遇记录。角色触发的奇遇事件记录。
        endpoint: /event/records
        params: server, name(角色名), full(0=只返回已触发, 1=含未触发)
        """
        return await self._request("/event/records", server=server, name=name, full=full)

    async def event_missing(self, server: str, name: str) -> list:
        """未做奇遇。角色尚未触发的奇遇列表。
        endpoint: /event/missing
        params: server, name(角色名)
        """
        return await self._request("/event/missing", server=server, name=name)

    async def event_unfinished(self, server: str, name: str) -> list:
        """未做奇遇别名（向后兼容）"""
        return await self.event_missing(server=server, name=name)

    async def event_recent(self, server: str, limit: int = 20) -> list:
        """近期奇遇。某服最近触发的奇遇事件列表。
        endpoint: /event/recent
        params: server, limit(默认20)
        """
        return await self._request("/event/recent", server=server, limit=limit)

    async def event_statistics(self, server: str = "", name: str = "", limit: int = 20) -> Any:
        """奇遇统计。某奇遇最近的触发记录。
        endpoint: /event/statistics
        params: server(可选), name(奇遇名称), limit(默认20)
        """
        return await self._request("/event/statistics", server=server, name=name, limit=limit)

    async def event_collect(self, server: str, num: int = 7) -> list:
        """奇遇汇总。白名单奇遇近 N 天触发次数与最新一条记录。
        endpoint: /event/collect
        params: server, num(天数, 默认7)
        """
        return await self._request("/event/collect", server=server, num=num)

    async def event_strategy(self, name: str) -> dict:
        """奇遇攻略。奇遇触发条件与流程白名单。
        endpoint: /event/strategy
        params: name(奇遇名称)
        """
        return await self._request("/event/strategy", name=name)

    # ============================================================
    # 8. 名剑竞技 (Arena)
    # ============================================================

    async def arena_recent(self, server: str, name: str, mode: int = 0) -> dict:
        """名剑战绩。角色竞技场战绩与历史表现。
        endpoint: /arena/recent
        params: server, name(角色名), mode(比赛模式, 默认0=全部模式, 可选22/33/55)
        """
        return await self._request("/arena/recent", server=server, name=name, mode=mode)

    async def arena_awesome(self, mode: int = 33, limit: int = 20) -> list:
        """名剑排行。某比赛模式竞技场前 limit 名排行。
        endpoint: /arena/awesome
        params: mode(比赛模式, 默认33), limit(显示数量, 默认20)
        """
        return await self._request("/arena/awesome", mode=mode, limit=limit)

    async def arena_schools(self, mode: int = 33) -> list:
        """名剑统计。某比赛模式下各门派竞技场周统计。
        endpoint: /arena/schools
        params: mode(比赛模式, 默认33)
        """
        return await self._request("/arena/schools", mode=mode)

    # ============================================================
    # 9. 物价交易 (Trade & Auction)
    # ============================================================

    async def trade_demon(self, server: str = "", limit: int = 30) -> list:
        """金价行情。各渠道金币比价。
        endpoint: /trade/demon
        params: server, limit(默认30)
        """
        return await self._request("/trade/demon", server=server, limit=limit)

    async def trade_records(self, name: str, server: str = "") -> Any:
        """物品价格。各区/指定服外观历史成交记录。
        endpoint: /trade/records
        params: name(物品名称), server(可选)
        """
        return await self._request("/trade/records", name=name, server=server)

    async def trade_item_search(self, name: str) -> list:
        """外观搜索。按名称搜索外观物品。
        endpoint: /trade/item/search
        params: name(物品名称)
        """
        return await self._request("/trade/item/search", name=name)

    async def trade_item_records(self, name: str, server: str = "") -> dict:
        """外观价格趋势。定位外观后取历史成交与万宝楼挂单。
        endpoint: /trade/item/records
        params: name(物品名称), server(可选)
        """
        return await self._request("/trade/item/records", name=name, server=server)

    async def trade_manufacture(self, server: str, name: str, source: int = 0) -> dict:
        """成本计算。成品配方算材料成本。
        endpoint: /trade/manufacture
        params: server, name(成品名称), source(0=交易行/1=jx3box)
        """
        return await self._request("/trade/manufacture", server=server, name=name, source=source)

    async def trade_wanbaolou(self, id: str) -> dict:
        """编号搜索。按角色编号查万宝楼详情。
        endpoint: /trade/wanbaolou
        params: id(角色编号)
        """
        return await self._request("/trade/wanbaolou", id=id)

    async def auction_records(self, server: str, name: Optional[str] = None, limit: int = 50) -> Any:
        """阵营拍卖。按大区查竞拍记录。
        endpoint: /auction/records
        params: server, name(物品名称, 可选), limit(数量, 默认50)
        """
        return await self._request("/auction/records", server=server, name=name, limit=limit)

    # ============================================================
    # 10. 阵营与帮会 (Camp, Battle, Wicked)
    # ============================================================

    async def battle_records(self, server: str) -> Any:
        """帮战记录。查询服务器最近帮战。
        endpoint: /battle/records
        params: server
        """
        return await self._request("/battle/records", server=server)

    async def sand_records(self, server: str) -> dict:
        """阵营沙盘。各据点归属帮会/阵营及防守情况。
        endpoint: /sand/records
        params: server
        """
        return await self._request("/sand/records", server=server)


    async def wicked_records(self, server: str = "", limit: int = 20) -> list:
        """诛恶事件。恶人诛恶刷新记录。
        endpoint: /wicked/records
        params: server(可选), limit(默认20)
        """
        return await self._request("/wicked/records", server=server, limit=limit)

    async def smite_records(self, server: str = "") -> list:
        """诛恶记录别名（向后兼容）"""
        return await self.wicked_records(server=server)

    async def castle_status(self) -> Any:
        """关隘首领。各服关隘首领当前状态。
        endpoint: /castle/status
        """
        return await self._request("/castle/status")

    async def mine_cart(self, server: str = "") -> Any:
        """关隘首领别名（向后兼容）"""
        return await self.castle_status()

    async def monster_weekly(self) -> dict:
        """百战首领。本周百战异闻录首领列表及 buff。
        endpoint: /monster/weekly
        """
        return await self._request("/monster/weekly")

    async def active_monster(self) -> dict:
        """百战首领别名（向后兼容）"""
        return await self.monster_weekly()

    async def active_next_event(self) -> dict:
        """扶摇预测别名（向后兼容）"""
        # 最新 JX3API 接口中扶摇预测并入日历或下线，优雅返回空结构避免异常
        return {}

    # ============================================================
    # 11. 排行榜单 (Rank)
    # ============================================================

    async def rank_statistics(self, server: str = "", name: str = "") -> list:
        """排行统计。查询指定榜单数据。
        endpoint: /rank/statistics
        params: server(可选), name(榜单名称)
        """
        return await self._request("/rank/statistics", server=server, name=name)

    async def rank_statistical(self, server: str, type: str = "个人") -> list:
        """本服榜单别名（向后兼容）"""
        return await self.rank_statistics(server=server, name=type)

    async def rank_trials(self, server: str = "", school: str = "") -> list:
        """试炼之地。试炼排行。
        endpoint: /rank/trials
        params: server(可选), name(门派/心法名称)
        """
        return await self._request("/rank/trials", server=server, name=school)

    async def rank_arena(self, server: str = "", mode: int = 0) -> list:
        """跨服名剑。军团赛季战绩榜。
        endpoint: /rank/arena
        params: server(可选), mode(0=2v2, 1=3v3, 2=5v5)
        """
        return await self._request("/rank/arena", server=server, mode=mode)

    async def rank_championship(self, server: str = "", camp: int = 1) -> list:
        """武林争霸。帮会争霸赛季榜。
        endpoint: /rank/championship
        params: server(可选), camp(1=浩气, 2=恶人)
        """
        return await self._request("/rank/championship", server=server, camp=camp)

    async def rank_constable(self, server: str = "") -> list:
        """捕快荣誉榜。
        endpoint: /rank/constable
        params: server(可选)
        """
        return await self._request("/rank/constable", server=server)

    async def rank_outlaw(self, server: str = "") -> list:
        """江湖浪客榜。
        endpoint: /rank/outlaw
        params: server(可选)
        """
        return await self._request("/rank/outlaw", server=server)

    async def rank_wanted(self, server: str = "", mode: int = 1) -> list:
        """决斗挑战榜。
        endpoint: /rank/wanted
        params: server(可选), mode(1=公开, 2=私密)
        """
        return await self._request("/rank/wanted", server=server, mode=mode)

    async def reward_statistics(self, server: str = "", name: str = "", limit: int = 20) -> Any:
        """掉落统计。副本掉落物品统计。
        endpoint: /reward/statistics
        params: server(可选), name(物品/副本名), limit(默认20)
        """
        return await self._request("/reward/statistics", server=server, name=name, limit=limit)

    # ============================================================
    # 12. 副本与秘境 (Dungeon & Mech)
    # ============================================================

    async def mech_decrypt(self) -> dict:
        """秘境方位。推算秘境方位与倒计时。
        endpoint: /mech/decrypt
        """
        return await self._request("/mech/decrypt")

    async def mech_calculator(self, name: str = "") -> dict:
        """副本解密别名（向后兼容）"""
        return await self.mech_decrypt()

    async def trial_bosses(self, season: str, floor: int) -> dict:
        """秒伤计算。试炼之地各 BOSS 血量与秒伤。
        endpoint: /trial/bosses
        params: season, floor
        """
        return await self._request("/trial/bosses", season=season, floor=floor)

    async def trial_seasons(self) -> list:
        """赛季列表。试炼之地全部赛季。
        endpoint: /trial/seasons
        """
        return await self._request("/trial/seasons")

    async def tuilan_achievement(
        self, server: str, name: str, class_: int = 1, subclass: Optional[str] = None
    ) -> dict:
        """资历分布。角色资历完成度汇总。
        endpoint: /tuilan/achievement
        params: server, name, class, subclass
        """
        return await self._request(
            "/tuilan/achievement",
            server=server,
            name=name,
            **{"class": class_, "subclass": subclass},
        )

    # ============================================================
    # 13. 社区与娱乐 (Community & Misc)
    # ============================================================

    async def recruit_search(self, server: str, keyword: str = "", type: int = 1, limit: int = 50) -> Any:
        """团队招募。查询团队招募信息。
        endpoint: /recruit/search
        params: server, keyword(可选), label(1=本服+跨服, 2=本服, 3=跨服), limit
        """
        return await self._request("/recruit/search", server=server, keyword=keyword, label=type, limit=limit)

    async def mentor_search(self, server: str, keyword: str = "", label: int = 1, limit: int = 50) -> Any:
        """师徒相关。查询师徒招募信息。
        endpoint: /mentor/search
        params: server, keyword(可选), label(1=拜师/2=收徒), limit
        """
        return await self._request("/mentor/search", server=server, keyword=keyword, label=label, limit=limit)

    async def fraud_detail(self, uin: int, server: str = "") -> Any:
        """骗子查询。查询 UID/QQ 是否在骗子风控库中。
        endpoint: /fraud/detail
        params: uid(角色UID/QQ号), server(可选)
        """
        return await self._request("/fraud/detail", uid=uin, server=server)

    async def duowan_statistics(self, server: str = "") -> dict:
        """统战歪歪。查询各服 YY 语音频道在线主播。
        endpoint: /duowan/statistics
        params: server(可选)
        """
        return await self._request("/duowan/statistics", server=server)

    async def tieba_random(self, tags: str = "818", server: str = "", limit: int = 10) -> dict:
        """百度贴吧。随机取近 31 天贴吧帖子。
        endpoint: /tieba/random
        params: tags(帖子类型, 默认818), server(可选), limit
        """
        return await self._request("/tieba/random", tags=tags, server=server, limit=limit)

    async def tieba_item_records(self, name: str, server: str = "", limit: int = 10) -> dict:
        """贴吧物价。在贴吧楼层搜相关外观帖子。
        endpoint: /tieba/item/records
        params: name(物品名), server(可选), limit
        """
        return await self._request("/tieba/item/records", name=name, server=server, limit=limit)

    async def saohua_random(self) -> dict:
        """随机骚话。从骚话库随机取一条。
        endpoint: /saohua/random
        """
        return await self._request("/saohua/random")

    async def saohua_content(self) -> dict:
        """舔狗日志。从舔狗日志库随机取一条。
        endpoint: /saohua/content
        """
        return await self._request("/saohua/content")

    async def saohua_context(self, name: str) -> dict:
        """分类语录。疯狂星期四/彩虹屁/毒鸡汤/朋友圈等。
        endpoint: /saohua/context
        params: name(分类名)
        """
        return await self._request("/saohua/context", name=name)

    async def saohua_answer(self) -> dict:
        """答案之书。从答案之书抽 1 条答案与鼓励语。
        endpoint: /saohua/answer
        """
        return await self._request("/saohua/answer")

    async def saohua_drink(self) -> dict:
        """喝什么。随机抽取饮品推荐。
        endpoint: /saohua/drink
        """
        return await self._request("/saohua/drink")

    async def saohua_eat(self) -> dict:
        """吃什么。随机抽取美食推荐。
        endpoint: /saohua/eat
        """
        return await self._request("/saohua/eat")

    async def saohua_zhanan(self) -> dict:
        """渣男语录。从渣男语录库随机取一条。
        endpoint: /saohua/zhanan
        """
        return await self._request("/saohua/zhanan")


# 模块级单例
api_client = JX3APIClient()
