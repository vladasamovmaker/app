import re
from datetime import datetime
from typing import Optional


def extract_price(text: str) -> Optional[float]:
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{1,2})?)",
        r"([\d,]+(?:\.\d{1,2})?)\s*(?:TON|USD|EUR|RUB|руб|₽|\$|€)",
        r"\b([\d]{2,}(?:[.,]\d+)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


SOURCE_ICONS = {
    "tonnel": "🔵",
    "portals": "🟣",
    "mrkt": "🟡",
    "demo_feed": "📰",
}


def format_post(post: dict) -> str:
    source = post.get("source", "")
    icon = SOURCE_ICONS.get(source.lower(), "🎁")
    price = post.get("price")
    price_str = f"<b>{price:.2f} TON</b>" if price else "<i>цена не указана</i>"
    ts: datetime = post.get("timestamp")
    date_str = ts.strftime("%d.%m %H:%M") if ts else "—"
    name = truncate(post.get("text", ""), 120)
    link = post.get("link", "")

    lines = [
        f"{icon} {name}",
        f"💰 {price_str}  •  🕐 {date_str}",
    ]
    if link:
        lines.append(f'<a href="{link}">👉 Открыть на маркете</a>')
    return "\n".join(lines)


def format_posts_list(posts: list, title: str = "") -> str:
    if not posts:
        return "😔 <b>Ничего не найдено</b>\n\nПопробуй позже или измени фильтр."
    parts = [format_post(p) for p in posts]
    body = "\n\n┄┄┄┄┄┄┄┄┄┄\n\n".join(parts)
    if title:
        return f"{title}\n\n{body}"
    return body


def format_stats(s: dict, users: int = 0, subs: int = 0) -> str:
    avg = f"{s['avg_price']:.2f} TON" if s.get("avg_price") else "—"
    mn = f"{s['min_price']:.2f} TON" if s.get("min_price") else "—"
    mx = f"{s['max_price']:.2f} TON" if s.get("max_price") else "—"
    return (
        "📊 <b>Статистика рынка</b>\n\n"
        f"🎁 Лотов в базе: <b>{s.get('total', 0)}</b>\n"
        f"💰 Средняя цена: <b>{avg}</b>\n"
        f"⬇️ Минимум: <b>{mn}</b>\n"
        f"⬆️ Максимум: <b>{mx}</b>\n\n"
        f"👤 Пользователей: <b>{users}</b>\n"
        f"🔔 Подписчиков: <b>{subs}</b>"
    )
