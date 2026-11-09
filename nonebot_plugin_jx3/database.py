import os
from pathlib import Path
from typing import Optional, List

from tinydb import TinyDB, Query


def _resolve_data_dir() -> Path:
    """解析数据存储目录，优先使用挂载的 data 目录保证数据持久化"""
    # 1. 显式指定的环境变量优先
    env_dir = os.getenv("JX3_DATA_DIR") or os.getenv("LOCALSTORE_DATA_DIR")
    if env_dir:
        p = Path(env_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 2. 优先使用当前工作目录下的 data 目录（Docker volume 挂载的 /app/data）
    app_data = Path("data").resolve()
    try:
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    except Exception:
        pass

    # 3. 兜底使用 localstore 系统存储目录
    try:
        import nonebot_plugin_localstore as store
        p = store.get_plugin_data_dir()
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        p = Path(__file__).parent / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p


DATA_DIR = _resolve_data_dir()


class JX3Database:
    def __init__(self):
        self.bind_db = TinyDB(DATA_DIR / "jx3_bind.json")
        self.sub_db = TinyDB(DATA_DIR / "jx3_subscribe.json")
        self._Q = Query()

    # ==================== 服务器绑定 ====================

    async def get_server(self, group_id: int) -> Optional[str]:
        """获取群绑定的服务器名"""
        result = self.bind_db.search(self._Q.group_id == group_id)
        return result[0]["server"] if result else None

    async def set_server(self, group_id: int, server: str):
        """设置/更新群绑定的服务器"""
        if await self.get_server(group_id):
            self.bind_db.update({"server": server}, self._Q.group_id == group_id)
        else:
            self.bind_db.insert({"group_id": group_id, "server": server})

    async def get_groups_by_server(self, server: str) -> List[int]:
        """获取绑定了指定服务器的所有群号"""
        results = self.bind_db.search(self._Q.server == server)
        return [r["group_id"] for r in results]

    # ==================== 订阅管理 ====================

    # 所有可订阅的事件名称
    SUBSCRIBE_NAMES = [
        "奇遇", "绝世奇遇", "抓马", "扶摇", "诛恶", "玄晶",
        "烟花", "的卢", "追魂", "祭天", "阵营拍卖",
        "开服", "新闻", "更新", "818", "八卦", "微博",
        "攻防实况", "阵营活动提醒",
        "关隘", "云丛",
    ]

    async def get_subscribes(self, group_id: int) -> List[str]:
        """获取群的订阅列表"""
        result = self.sub_db.search(self._Q.group_id == group_id)
        if result:
            # 兼容旧格式：字段名可能是 "subscribe" 或 "subscribes"
            return result[0].get("subscribes", result[0].get("subscribe", []))
        return []

    async def add_subscribe(self, group_id: int, name: str) -> bool:
        """添加订阅。返回 True=成功, False=已存在"""
        if name == "八卦":
            name = "818"
        current = await self.get_subscribes(group_id)
        if name in current:
            return False
        new_list = current + [name]
        if current:
            self.sub_db.update({"subscribes": new_list}, self._Q.group_id == group_id)
        else:
            self.sub_db.insert({"group_id": group_id, "subscribes": new_list})
        return True

    async def remove_subscribe(self, group_id: int, name: str) -> bool:
        """移除订阅。返回 True=成功, False=不存在"""
        if name == "八卦":
            name = "818"
        current = await self.get_subscribes(group_id)
        if name not in current:
            return False
        current.remove(name)
        self.sub_db.update({"subscribes": current}, self._Q.group_id == group_id)
        return True

    async def get_groups_by_subscribe(self, subscribe: str) -> List[int]:
        """获取订阅了指定事件的所有群号"""
        # 兼容旧格式
        results_new = self.sub_db.search(
            self._Q.subscribes.test(lambda s: subscribe in s)
        )
        results_old = self.sub_db.search(
            self._Q.subscribe.test(lambda s: subscribe in s)
        )
        group_ids = set()
        for r in results_new + results_old:
            group_ids.add(r["group_id"])
        return list(group_ids)


# 模块级单例
db = JX3Database()
