from dataclasses import dataclass
from typing import List


@dataclass
class ParserSource:
    name: str
    url: str
    source_type: str  # "rss", "telegram_web", "tonnel_api", "portals_api", "mrkt_api"
    enabled: bool = True


SOURCES: List[ParserSource] = [
    ParserSource(
        name="tonnel",
        url="https://tonnel.network/marketplace",
        source_type="tonnel_api",
        enabled=True,
    ),
    ParserSource(
        name="portals",
        url="https://portals.ton/marketplace",
        source_type="portals_api",
        enabled=True,
    ),
    ParserSource(
        name="mrkt",
        url="https://mrkt.ton/marketplace",
        source_type="mrkt_api",
        enabled=True,
    ),
    ParserSource(
        name="mrkt_channel",
        url="https://t.me/s/mrktnotification",
        source_type="telegram_web",
        enabled=True,
    ),
]
