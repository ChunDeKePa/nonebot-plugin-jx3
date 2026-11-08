from pydantic import BaseModel
from typing import List, Any

try:
    from pydantic import field_validator

    class _BaseConfig(BaseModel):
        @field_validator("jx3_enabled_groups", mode="before", check_fields=False)
        @classmethod
        def _parse_groups(cls, v: Any) -> List[int]:
            if not v:
                return []
            if isinstance(v, str):
                v = v.strip().strip("[]").strip()
                if not v:
                    return []
                return [int(x.strip().strip("'\"")) for x in v.split(",") if x.strip()]
            if isinstance(v, (list, tuple, set)):
                return [int(x) for x in v if str(x).strip()]
            if isinstance(v, int):
                return [v]
            return []
except ImportError:
    from pydantic import validator

    class _BaseConfig(BaseModel):
        @validator("jx3_enabled_groups", pre=True, allow_reuse=True)
        def _parse_groups(cls, v: Any) -> List[int]:
            if not v:
                return []
            if isinstance(v, str):
                v = v.strip().strip("[]").strip()
                if not v:
                    return []
                return [int(x.strip().strip("'\"")) for x in v.split(",") if x.strip()]
            if isinstance(v, (list, tuple, set)):
                return [int(x) for x in v if str(x).strip()]
            if isinstance(v, int):
                return [v]
            return []


class Config(_BaseConfig):
    """插件配置，在 .env 或 bot 配置文件中设置"""

    # ====== HTTP API ======
    jx3api_key: str = ""
    """站点访问令牌 (token)。VIP 接口必需。"""

    jx3api_token: str = ""
    """站点访问令牌 (token) 别名配置项。"""

    jx3_tuilan_ticket: str = ""
    """推栏 ticket。名剑大会相关接口必需。"""

    # ====== WebSocket 推送 ======
    jx3wss_token: str = ""
    """WSS 身份验证令牌（单服75/月，全服200/月）。
    通过连接时的 HTTP Header {"token": xxx} 传递。
    大部分推送事件都需要此 token 才能接收。
    与 jx3api_key 是独立购买的服务。"""

    # ====== 群控制 ======
    jx3_enabled_groups: List[int] = []
    """群号白名单。为空=所有群可用，非空=仅列表中的群可用。"""

    # ====== 通用 ======
    jx3_bot_name: str = "水水"
    """API 图片中显示的 bot 名称。"""

    jx3api_base_url: str = "https://www.jx3api.com"
    """JX3API HTTP 基础 URL。"""

    jx3_wss_url: str = "wss://socket.nicemoe.cn"
    """JX3API WebSocket 地址。"""

    jx3_default_server: str = ""
    """默认服务器，当群未绑定时使用。"""