"""HTML→图片渲染引擎（集成高可用模板容错与智能图片多级缓存）"""
import datetime
import time
from pathlib import Path
from typing import Optional, Dict, Tuple

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from nonebot import logger

try:
    from nonebot_plugin_htmlrender import html_to_pic
except ImportError:
    # 兼容 nonebot-plugin-htmlrender >= 0.8.0 新架构 API
    from nonebot_plugin_htmlrender import render_html

    async def html_to_pic(html: str, viewport: dict = None, wait: int = 0, template_path: str = None) -> bytes:
        width = viewport.get("width", 600) if viewport else 600
        image = await render_html(html, width=width)
        return bytes(image)

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _format_ts(value):
    """Jinja2 过滤器：Unix 时间戳 → 可读日期"""
    try:
        ts = int(value)
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%m-%d %H:%M")
    except (ValueError, TypeError, OSError):
        return str(value)


# ============================================================
# 缓存与时间工具函数（剑网三以每日 07:00 为刷新分界点）
# ============================================================

def get_game_day_str() -> str:
    """获取当前剑网三游戏日标识（每天 07:00 刷新日常与活动）"""
    now = datetime.datetime.now()
    if now.hour < 7:
        now = now - datetime.timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def get_game_day_ttl() -> float:
    """计算距离下一个剑网三游戏日刷新时刻（07:00:05）的剩余秒数"""
    now = datetime.datetime.now()
    reset_today = now.replace(hour=7, minute=0, second=5, microsecond=0)
    if now >= reset_today:
        target = reset_today + datetime.timedelta(days=1)
    else:
        target = reset_today
    return max(60.0, (target - now).total_seconds())


def get_weekly_ttl(target_weekday: int = 0) -> float:
    """计算距离下一次指定周常结算时刻（07:00:05，0=周一，1=周二）的剩余秒数"""
    now = datetime.datetime.now()
    days_ahead = (target_weekday - now.weekday()) % 7
    target = (now + datetime.timedelta(days=days_ahead)).replace(hour=7, minute=0, second=5, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=7)
    return max(60.0, (target - now).total_seconds())


# ============================================================
# 图片内存缓存管理器 (LRU + TTL + 前缀失效)
# ============================================================

class ImageCache:
    """图片渲染缓存管理器。
    支持内存高速缓存 (LRU/TTL) 与业务场景精准失效（如更新群绑定或订阅时）。
    """

    def __init__(self, max_size: int = 500):
        # key -> (image_bytes, expire_at)
        self._cache: Dict[str, Tuple[bytes, Optional[float]]] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[bytes]:
        """获取未过期的缓存数据，若已过期则自动删除"""
        if key not in self._cache:
            return None
        data, expire_at = self._cache[key]
        if expire_at is not None and time.time() > expire_at:
            del self._cache[key]
            return None
        return data

    def set(self, key: str, data: bytes, ttl: Optional[float] = None) -> None:
        """存入缓存数据，ttl 为存活秒数（None 表示常驻直到进程重启）"""
        if len(self._cache) >= self._max_size:
            self._cleanup()
        expire_at = (time.time() + ttl) if ttl is not None else None
        self._cache[key] = (data, expire_at)

    def invalidate(self, prefix_or_key: str) -> int:
        """使匹配指定前缀或精确键的缓存失效，返回被删除的条目数"""
        to_del = [k for k in self._cache if k == prefix_or_key or k.startswith(prefix_or_key + ":")]
        for k in to_del:
            del self._cache[k]
        if to_del:
            logger.debug(f"[JX3] 使图片缓存失效: {prefix_or_key} (共清理 {len(to_del)} 项)")
        return len(to_del)

    def _cleanup(self) -> None:
        """清理已过期缓存，若超限淘汰最早的 20% 条目"""
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if exp is not None and now > exp]
        for k in expired:
            del self._cache[k]
        if len(self._cache) >= self._max_size:
            keys_to_evict = list(self._cache.keys())[: max(1, self._max_size // 5)]
            for k in keys_to_evict:
                del self._cache[k]

    def clear(self) -> None:
        """清空全部缓存"""
        self._cache.clear()


# ============================================================
# 内置关键模板兜底恢复机制（防止热更或未全量构建时丢失文件）
# ============================================================

BUILTIN_SUBSCRIBE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 760px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #e0e0e0;
    padding: 24px;
  }
  .card {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
  }
  .main-title {
    font-size: 26px;
    font-weight: bold;
    color: #d4af37;
    text-align: center;
    padding-bottom: 8px;
    margin-bottom: 12px;
  }
  .info-bar {
    display: flex;
    justify-content: space-around;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(212, 175, 55, 0.2);
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 20px;
    font-size: 14px;
  }
  .info-item { display: flex; align-items: center; gap: 8px; }
  .info-label { color: rgba(255, 255, 255, 0.6); }
  .info-value { color: #ffd54f; font-weight: bold; }
  .info-value.unbound { color: #ef5350; }
  .section-title {
    font-size: 16px;
    font-weight: bold;
    color: #ffd54f;
    margin: 16px 0 10px 0;
    padding-left: 10px;
    border-left: 3px solid #d4af37;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .current-box {
    background: rgba(0, 0, 0, 0.2);
    border: 1px dashed rgba(212, 175, 55, 0.25);
    border-radius: 8px;
    padding: 14px;
    min-height: 52px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
  }
  .sub-tag-active {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(76, 175, 80, 0.2);
    border: 1px solid rgba(76, 175, 80, 0.5);
    color: #81c784;
    padding: 4px 12px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: bold;
  }
  .sub-tag-active::before { content: "●"; color: #4caf50; font-size: 11px; }
  .empty-tip { color: rgba(255, 255, 255, 0.4); font-size: 13px; width: 100%; text-align: center; padding: 8px 0; }
  .event-category-title { font-size: 14px; font-weight: bold; color: #90caf9; margin: 14px 0 6px 4px; display: flex; align-items: center; gap: 6px; }
  .event-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .event-item {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .event-name { font-weight: bold; font-size: 13px; color: #e0e0e0; display: flex; align-items: center; gap: 6px; }
  .event-desc { font-size: 12px; color: rgba(255, 255, 255, 0.55); margin-left: 8px; flex-grow: 1; text-align: right; }
  .event-scope { font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-left: 8px; flex-shrink: 0; }
  .scope-server { background: rgba(33, 150, 243, 0.15); color: #64b5f6; border: 1px solid rgba(33, 150, 243, 0.3); }
  .scope-all { background: rgba(255, 152, 0, 0.15); color: #ffb74d; border: 1px solid rgba(255, 152, 0, 0.3); }
  .guide-box {
    background: rgba(212, 175, 55, 0.08);
    border: 1px solid rgba(212, 175, 55, 0.25);
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 20px;
    font-size: 13px;
    line-height: 1.8;
  }
  .guide-title { font-weight: bold; color: #ffd54f; margin-bottom: 4px; font-size: 14px; }
  .cmd-chip {
    background: rgba(0, 0, 0, 0.4);
    color: #90caf9;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: Consolas, Monaco, monospace;
    font-size: 12px;
    margin-right: 6px;
  }
  .footer { text-align: center; color: rgba(255, 255, 255, 0.35); font-size: 12px; margin-top: 14px; }
</style>
</head>
<body>
  <div class="card">
    <div class="main-title">🔔 剑网三助手 · 订阅与推送管理</div>
    <div class="info-bar">
      <div class="info-item">
        <span class="info-label">本群绑定服务器：</span>
        {% if server and server != "未绑定" %}
          <span class="info-value">【{{ server }}】</span>
        {% else %}
          <span class="info-value unbound">未绑定（请发送「绑定 <区服>」）</span>
        {% endif %}
      </div>
      <div class="info-item">
        <span class="info-label">当前群号：</span>
        <span class="info-value">{{ group_id }}</span>
      </div>
    </div>

    <div class="section-title">
      <span>📋 本群已开启的推送项目</span>
      <span style="font-size: 12px; color: rgba(255,255,255,0.5);">共 {{ current | length }} 项已生效</span>
    </div>
    <div class="current-box">
      {% if current and current | length > 0 %}
        {% for sub in current %}
          <span class="sub-tag-active">{{ sub }}</span>
        {% endfor %}
      {% else %}
        <div class="empty-tip">本群当前尚未开启任何事件推送。发送「订阅 <事件名>」即可开启！</div>
      {% endif %}
    </div>

    <div class="section-title">📢 支持订阅的全部事件目录</div>

    <div class="event-category-title">🌟 奇遇与奇珍</div>
    <div class="event-grid">
      <div class="event-item"><span class="event-name">奇遇</span><span class="event-desc">单服奇遇触发实时广播</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">绝世奇遇</span><span class="event-desc">单服绝世奇遇触发特别播报</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">扶摇</span><span class="event-desc">扶摇九天奇遇开启即时提醒</span><span class="event-scope scope-server">单服</span></div>
    </div>

    <div class="event-category-title">🐎 马匹与捕获</div>
    <div class="event-grid">
      <div class="event-item"><span class="event-name">抓马</span><span class="event-desc">马场龙子/麟驹/赤兔刷新与捕获</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">的卢</span><span class="event-desc">单服的卢出世、捕获与拍卖播报</span><span class="event-scope scope-server">单服</span></div>
    </div>

    <div class="event-category-title">⚔️ 阵营与攻防</div>
    <div class="event-grid">
      <div class="event-item"><span class="event-name">关隘</span><span class="event-desc">烂柯山关隘首领冷却与刷新</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">云丛</span><span class="event-desc">云丛事件开启倒计时与预告</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">攻防实况</span><span class="event-desc">大小攻防战况、据点、首领击退</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">阵营活动提醒</span><span class="event-desc">周二周四阵营活动、粮仓提醒</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">诛恶</span><span class="event-desc">恶人谷诛恶事件刷新广播</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">阵营拍卖</span><span class="event-desc">攻防拍卖极品装备通告</span><span class="event-scope scope-server">单服</span></div>
    </div>

    <div class="event-category-title">📰 官方动态与开服</div>
    <div class="event-grid">
      <div class="event-item"><span class="event-name">开服</span><span class="event-desc">服务器维护完成开服极速通知</span><span class="event-scope scope-server">单服</span></div>
      <div class="event-item"><span class="event-name">新闻</span><span class="event-desc">官方最新新闻资讯即时推送</span><span class="event-scope scope-all">全服</span></div>
      <div class="event-item"><span class="event-name">更新</span><span class="event-desc">版本更新与客户端补丁发布通知</span><span class="event-scope scope-all">全服</span></div>
      <div class="event-item"><span class="event-name">微博</span><span class="event-desc">剑网3官方微博最新动态推送</span><span class="event-scope scope-all">全服</span></div>
    </div>

    <div class="event-category-title">💬 江湖八卦与全服通告</div>
    <div class="event-grid">
      <div class="event-item"><span class="event-name">818 / 八卦</span><span class="event-desc">贴吧最新 818/吐槽/树洞精华速递</span><span class="event-scope scope-all">全服</span></div>
      <div class="event-item"><span class="event-name">玄晶</span><span class="event-desc">全服大铁玄晶掉落全服通告</span><span class="event-scope scope-all">全服</span></div>
      <div class="event-item"><span class="event-name">烟花</span><span class="event-desc">全服绝世烟花通告</span><span class="event-scope scope-all">全服</span></div>
      <div class="event-item"><span class="event-name">追魂 / 祭天</span><span class="event-desc">全服追魂帖、祭天城管广播</span><span class="event-scope scope-all">全服</span></div>
    </div>

    <div class="guide-box">
      <div class="guide-title">💡 快捷操作指南</div>
      <div><span class="cmd-chip">订阅 <事件名></span>开启指定推送（例：<code>订阅 开服</code>、<code>订阅 奇遇</code>）</div>
      <div><span class="cmd-chip">取消订阅 <事件名></span>关闭指定推送（例：<code>取消订阅 818</code>）</div>
      <div style="margin-top: 6px; color: rgba(255,255,255,0.7); font-size: 12px;">
        📌 说明：标记为 <span class="event-scope scope-server" style="padding:1px 4px;">单服</span> 的事件需先通过 <span class="cmd-chip">绑定 <服务器></span> 绑定本群服务器；仅群主与管理员可修改设置。
      </div>
    </div>
  </div>
  <div class="footer">{{ bot_name }} · JX3API 实时推送服务</div>
</body>
</html>
"""

BUILTIN_TEMPLATES: Dict[str, str] = {
    "subscribe.html": BUILTIN_SUBSCRIBE_HTML
}


class JX3Renderer:
    def __init__(self):
        self.cache = ImageCache()
        # 自动保障内置关键模板存在于磁盘
        self._ensure_builtin_templates()
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True
        )
        self.env.filters["format_ts"] = _format_ts

    def _ensure_builtin_templates(self):
        """如果磁盘中丢失关键内置模板（如容器未重新打包），自动恢复文件"""
        try:
            TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
            for name, content in BUILTIN_TEMPLATES.items():
                p = TEMPLATE_DIR / name
                if not p.exists():
                    p.write_text(content, encoding="utf-8")
                    logger.info(f"[JX3] 自动恢复内置模板文件: {name}")
        except Exception as e:
            logger.warning(f"[JX3] 检查内置模板文件异常: {e}")

    async def render(
        self,
        template_name: str,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[float] = None,
        **kwargs
    ) -> bytes:
        """渲染 Jinja2 模板为 PNG 图片字节，并支持多级智能图片缓存。

        Args:
            template_name: 模板文件名，如 "calendar.html"
            cache_key: 缓存键名。若传入且命中缓存，将跳过 Playwright 渲染瞬间返回（0ms 消耗）
            cache_ttl: 缓存存活时长（秒），传 None 则常驻直到进程重启
            **kwargs: 传递给模板的数据

        Returns:
            PNG 图片的 bytes
        """
        # 1. 优先命中图片内存缓存
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"[JX3] 命中图片渲染缓存: {cache_key}")
                return cached

        from .config import plugin_config

        # 注入公共变量
        kwargs.setdefault("bot_name", plugin_config.jx3_bot_name)
        kwargs.setdefault("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

        # 2. 加载模板（带高可用容错保护）
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            if template_name in BUILTIN_TEMPLATES:
                logger.warning(f"[JX3] 模板 {template_name} 在磁盘不存在，采用内置备用模板编译")
                self._ensure_builtin_templates()
                template = self.env.from_string(BUILTIN_TEMPLATES[template_name])
            else:
                raise

        html = template.render(**kwargs)

        # 3. 视口宽度定制
        if "sand" in template_name:
            view_width = 1297
        elif "gold_trend" in template_name:
            view_width = 660
        elif "help" in template_name or "subscribe" in template_name:
            view_width = 760
        else:
            view_width = 600

        target_file = TEMPLATE_DIR / template_name
        template_uri = target_file.as_uri() if target_file.exists() else (TEMPLATE_DIR / "base.html").as_uri()

        # 4. Playwright 浏览器渲染
        img_bytes = await html_to_pic(
            html,
            viewport={"width": view_width, "height": 10},
            wait=0,
            template_path=template_uri,
        )

        # 5. 写入图片缓存
        if cache_key:
            self.cache.set(cache_key, img_bytes, ttl=cache_ttl)
            logger.debug(f"[JX3] 写入图片渲染缓存: {cache_key} (ttl={cache_ttl}s)")

        return img_bytes

    def invalidate(self, prefix_or_key: str) -> int:
        """根据前缀或完整键主动让缓存失效"""
        return self.cache.invalidate(prefix_or_key)


# 模块级单例
renderer = JX3Renderer()
