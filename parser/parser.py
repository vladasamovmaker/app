import asyncio
import hashlib
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

import aiohttp
from bs4 import BeautifulSoup

from parser.sources import ParserSource, SOURCES
from utils.helpers import extract_price
from utils.logger import get_logger

logger = get_logger(__name__)


def _make_id(source_name: str, link: str) -> str:
    return hashlib.md5(f"{source_name}:{link}".encode()).hexdigest()


# ── Tonnel API ─────────────────────────────────────────────────────────────

async def fetch_tonnel(session: aiohttp.ClientSession, source: ParserSource) -> List[dict]:
    posts = []
    try:
        url = "https://api.tonnel.network/gift/list"
        params = {"sort": "latest", "limit": 20, "type": "SALE"}
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                logger.warning(f"Tonnel API returned {resp.status}")
                return []
            data = await resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("gifts", []))
        for item in items:
            name = item.get("name") or item.get("gift_name") or item.get("title") or "Подарок"
            price_raw = item.get("price") or item.get("ton_price") or item.get("priceTon") or 0
            try:
                price = float(price_raw) / 1e9 if float(price_raw) > 1000 else float(price_raw)
            except Exception:
                price = None
            gift_id = str(item.get("id") or item.get("gift_id") or item.get("nft_id") or name)
            link = item.get("link") or item.get("url") or f"https://tonnel.network/gift/{gift_id}"
            posts.append({
                "id": _make_id("tonnel", gift_id),
                "text": name,
                "price": price,
                "link": link,
                "source": "tonnel",
                "timestamp": datetime.utcnow(),
            })
        logger.info(f"Tonnel API: {len(posts)} gifts")
    except Exception as exc:
        logger.error(f"Tonnel API error: {exc}")
    return posts


# ── Portals API ────────────────────────────────────────────────────────────

async def fetch_portals(session: aiohttp.ClientSession, source: ParserSource) -> List[dict]:
    posts = []
    try:
        url = "https://api.getgems.io/graphql"
        query = """
        {
          nftSearch(query: "", collections: [], sort: PRICE_ASC, first: 20) {
            edges {
              node {
                id
                name
                sale { price { value } }
                collection { name }
              }
            }
          }
        }
        """
        async with session.post(
            url,
            json={"query": query},
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status != 200:
                logger.warning(f"GetGems API returned {resp.status}")
                return []
            data = await resp.json()

        edges = (data.get("data") or {}).get("nftSearch", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            name = node.get("name") or "NFT Gift"
            sale = node.get("sale") or {}
            price_val = (sale.get("price") or {}).get("value")
            try:
                price = float(price_val) / 1e9 if price_val else None
            except Exception:
                price = None
            nft_id = node.get("id", name)
            link = f"https://getgems.io/nft/{nft_id}"
            posts.append({
                "id": _make_id("portals", nft_id),
                "text": name,
                "price": price,
                "link": link,
                "source": "portals",
                "timestamp": datetime.utcnow(),
            })
        logger.info(f"GetGems/Portals API: {len(posts)} gifts")
    except Exception as exc:
        logger.error(f"GetGems API error: {exc}")
    return posts


# ── MRKT Telegram channel (web) ────────────────────────────────────────────

async def fetch_telegram_web(session: aiohttp.ClientSession, source: ParserSource) -> List[dict]:
    posts = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
        }
        async with session.get(source.url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                logger.warning(f"Telegram web {source.name} returned {resp.status}")
                return []
            html = await resp.text()

        soup = BeautifulSoup(html, "lxml")
        messages = soup.select(".tgme_widget_message_wrap")[-20:]
        for msg in messages:
            text_el = msg.select_one(".tgme_widget_message_text")
            if not text_el:
                continue
            text = text_el.get_text(separator=" ", strip=True)
            if len(text) < 10:
                continue
            link_el = msg.select_one(".tgme_widget_message_date")
            link = link_el["href"] if link_el and link_el.get("href") else source.url
            price = extract_price(text)
            posts.append({
                "id": _make_id(source.name, link),
                "text": text[:500],
                "price": price,
                "link": link,
                "source": source.name,
                "timestamp": datetime.utcnow(),
            })
        logger.info(f"Telegram web {source.name}: {len(posts)} posts")
    except Exception as exc:
        logger.error(f"Telegram web {source.name} error: {exc}")
    return posts


# ── Dispatcher ─────────────────────────────────────────────────────────────

async def fetch_source(session: aiohttp.ClientSession, source: ParserSource) -> List[dict]:
    if source.source_type == "tonnel_api":
        return await fetch_tonnel(session, source)
    elif source.source_type in ("portals_api", "getgems_api"):
        return await fetch_portals(session, source)
    elif source.source_type == "telegram_web":
        return await fetch_telegram_web(session, source)
    else:
        logger.warning(f"Unknown source type: {source.source_type}")
        return []


async def run_parser() -> List[dict]:
    enabled = [s for s in SOURCES if s.enabled]
    if not enabled:
        logger.warning("No enabled sources")
        return []

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_source(session, src) for src in enabled]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_posts: List[dict] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Parser task failed: {result}")
        else:
            all_posts.extend(result)

    logger.info(f"Parser total: {len(all_posts)} raw posts")
    return all_posts
