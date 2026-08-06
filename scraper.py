import re
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from config import ALLOWED_DOMAINS


TIME_RANGE_PATTERN = re.compile(
    r"(?P<start>\d{1,2}:\d{2})"
    r"\s*[〜～~\-]\s*"
    r"(?P<end>\d{1,2}:\d{2})"
)

SCREEN_PATTERN = re.compile(
    r"スクリーン[０-９0-9]+"
    r"(?:\([^)]*\))?"
)

DATE_PATTERNS = (
    re.compile(
        r"(?P<year>20\d{2})[-_/]"
        r"(?P<month>\d{1,2})[-_/]"
        r"(?P<day>\d{1,2})"
    ),
    re.compile(
        r"(?P<year>20\d{2})"
        r"(?P<month>\d{2})"
        r"(?P<day>\d{2})"
    ),
)


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_DOMAINS
    )


def fetch_theater_page(url: str) -> dict:
    if not is_allowed_url(url):
        raise ValueError("許可されていないURLです。")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()

    if not is_allowed_url(response.url):
        raise ValueError(
            "公式ドメイン以外へ転送されたため、"
            "取得を中止しました。"
        )

    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else "タイトルなし"
    )

    return {
        "status_code": response.status_code,
        "title": title,
        "html_length": len(response.text),
        "final_url": response.url,
        "html": response.text,
    }


def _parse_date_candidate(
    candidate: str,
    selected_date: date,
) -> date | None:
    normalized = candidate.strip()

    for pattern in DATE_PATTERNS:
        match = pattern.search(normalized)

        if not match:
            continue

        try:
            return date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        except ValueError:
            continue

    month_day_pattern = re.compile(
        r"(?<!\d)"
        r"(?P<month>\d{1,2})\s*/\s*"
        r"(?P<day>\d{1,2})"
        r"(?!\d)"
    )
    match = month_day_pattern.search(normalized)

    if not match:
        return None

    month = int(match.group("month"))
    day = int(match.group("day"))

    for year in (
        selected_date.year,
        selected_date.year - 1,
        selected_date.year + 1,
    ):
        try:
            parsed = date(year, month, day)
        except ValueError:
            continue

        if abs((parsed - selected_date).days) <= 180:
            return parsed

    return None


def _attribute_text(tag: Tag) -> str:
    parts = []

    for key, value in tag.attrs.items():
        if isinstance(value, list):
            value_text = " ".join(
                str(item)
                for item in value
            )
        else:
            value_text = str(value)

        parts.append(f"{key}={value_text}")

    return " ".join(parts)


def _find_date_for_title(
    title_tag: Tag,
    selected_date: date,
) -> date | None:
    current: Tag | None = title_tag

    for _ in range(14):
        if current is None:
            break

        candidates = [
            _attribute_text(current),
        ]

        for selector in (
            "[data-date]",
            "[data-day]",
            "[class*='date']",
            "[class*='day']",
            "[id*='date']",
            "[id*='day']",
        ):
            element = current.select_one(selector)

            if element is None:
                continue

            candidates.append(
                element.get_text(
                    " ",
                    strip=True,
                )
            )
            candidates.append(
                _attribute_text(element)
            )

        for candidate in candidates:
            parsed = _parse_date_candidate(
                candidate,
                selected_date,
            )

            if parsed is not None:
                return parsed

        parent = current.parent
        current = (
            parent
            if isinstance(parent, Tag)
            else None
        )

    return None


def _find_single_movie_container(
    title_tag: Tag,
) -> Tag:
    """
    タイトルから上へたどり、
    「この作品タイトルを1つだけ含む最大の要素」を返す。

    次の作品タイトルを含む親へ到達する直前で止めるため、
    別作品の上映時刻が混ざらない。
    """
    current: Tag = title_tag
    best: Tag = title_tag

    for _ in range(14):
        parent = current.parent

        if not isinstance(parent, Tag):
            break

        titles = parent.select(
            "h3.schedule-movie-information-title"
        )

        if len(titles) > 1:
            break

        best = parent
        current = parent

    return best


def _match_requested_title(
    full_title: str,
    wanted_titles: list[str],
) -> str | None:
    return next(
        (
            wanted
            for wanted in wanted_titles
            if wanted in full_title
            or full_title in wanted
        ),
        None,
    )


def extract_humax_schedule_for_date(
    html: str,
    movie_titles: list[str],
    selected_date: date,
) -> list[dict]:
    """
    HUMAXのHTMLから、選択日・指定作品の上映回を抽出する。

    作品ごとに独立したコンテナだけを解析するため、
    他作品の上映時間は混入しない。
    """
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    wanted_titles = [
        title.strip()
        for title in movie_titles
        if title.strip()
    ]

    results = []
    seen = set()

    title_tags = soup.select(
        "h3.schedule-movie-information-title"
    )

    for title_tag in title_tags:
        full_title = title_tag.get_text(
            " ",
            strip=True,
        )

        matched_title = _match_requested_title(
            full_title,
            wanted_titles,
        )

        if matched_title is None:
            continue

        show_date = _find_date_for_title(
            title_tag,
            selected_date,
        )

        if show_date != selected_date:
            continue

        movie_container = _find_single_movie_container(
            title_tag
        )
        movie_text = movie_container.get_text(
            " ",
            strip=True,
        )

        for match in TIME_RANGE_PATTERN.finditer(
            movie_text
        ):
            start = match.group("start")
            end = match.group("end")

            nearby_text = movie_text[
                match.start():
                match.end() + 120
            ]

            screen_match = SCREEN_PATTERN.search(
                nearby_text
            )

            screen = (
                screen_match.group(0)
                if screen_match
                else ""
            )

            key = (
                matched_title,
                show_date.isoformat(),
                start,
                end,
                screen,
            )

            if key in seen:
                continue

            seen.add(key)

            results.append(
                {
                    "作品": matched_title,
                    "公式作品名": full_title,
                    "映画館": "池袋HUMAXシネマズ",
                    "上映日": show_date.isoformat(),
                    "開始": start,
                    "終了": end,
                    "スクリーン": screen,
                    "料金": 0,
                }
            )

    return sorted(
        results,
        key=lambda row: (
            row["開始"],
            row["作品"],
        ),
    )
