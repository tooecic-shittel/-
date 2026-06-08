import html
import os
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger


SUPPORTED_DOMAINS = (
    "douyin.com",
    "iesdouyin.com",
    "tiktok.com",
    "tiktokv.com",
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _extract_first_url(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0).rstrip("，,。.!！)") if match else text


def _normalize_douyin_modal_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not (host == "douyin.com" or host.endswith(".douyin.com")):
        return url

    query = parse_qs(parsed.query)
    modal_id = (query.get("modal_id") or query.get("aweme_id") or [""])[0]
    modal_id = re.sub(r"\D", "", modal_id or "")
    if not modal_id:
        return url

    # 抖音搜索页、精选页里的弹窗地址不是标准视频页，但 modal_id
    # 就是实际视频 ID。先转成标准视频页，yt-dlp/HTML 兜底才有机会解析。
    if "/search" in parsed.path or "/jingxuan/" in parsed.path:
        return f"https://www.douyin.com/video/{modal_id}"

    return url


def _validate_url(url: str) -> str:
    url = _extract_first_url(url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("请输入完整的抖音/TikTok 链接，例如 https://v.douyin.com/...")

    host = parsed.netloc.lower()
    if not any(host == domain or host.endswith(f".{domain}") for domain in SUPPORTED_DOMAINS):
        raise ValueError("当前只支持抖音或 TikTok 链接")
    return _normalize_douyin_modal_url(url)


def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def _extract_from_html(url: str) -> dict[str, Any]:
    response = requests.get(url, headers=_HEADERS, timeout=15, allow_redirects=True)
    response.raise_for_status()
    page = response.text

    title = _first_match(
        [
            r"<title[^>]*>(.*?)</title>",
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\'](.*?)["\']',
        ],
        page,
    )
    description = _first_match(
        [
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\'](.*?)["\']',
        ],
        page,
    )
    thumbnail = _first_match(
        [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](.*?)["\']',
        ],
        page,
    )
    video_url = _first_match(
        [
            r'<meta[^>]+property=["\']og:video(?::url)?["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+name=["\']twitter:player:stream["\'][^>]+content=["\'](.*?)["\']',
        ],
        page,
    )

    return {
        "source_url": url,
        "resolved_url": response.url,
        "webpage_url": response.url,
        "title": title,
        "description": description,
        "uploader": "",
        "duration": None,
        "tags": [],
        "thumbnail": thumbnail,
        "video_url": video_url,
        "extractor": "html",
        "downloaded_file": "",
    }


def _normalize_info(url: str, info: dict[str, Any], downloaded_file: str = "") -> dict[str, Any]:
    tags = info.get("tags") or info.get("categories") or []
    if isinstance(tags, str):
        tags = [tags]

    return {
        "source_url": url,
        "resolved_url": info.get("original_url") or info.get("webpage_url") or url,
        "webpage_url": info.get("webpage_url") or url,
        "title": info.get("title") or "",
        "description": info.get("description") or "",
        "uploader": info.get("uploader") or info.get("channel") or info.get("creator") or "",
        "duration": info.get("duration"),
        "tags": tags[:20],
        "thumbnail": info.get("thumbnail") or "",
        "video_url": info.get("url") or "",
        "extractor": info.get("extractor") or "yt-dlp",
        "downloaded_file": downloaded_file,
    }


def extract_video_info(
    url: str,
    download: bool = False,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Extract public Douyin/TikTok video metadata.

    Douyin extraction is intentionally best-effort because public share pages can
    require cookies, login, or anti-bot checks. yt-dlp handles most normal public
    links; the HTML fallback still gives the prompt generator useful context.
    """

    url = _validate_url(url)
    output_dir = output_dir or os.path.join(os.getcwd(), "storage", "douyin")

    try:
        import yt_dlp
    except ImportError:
        logger.warning("yt-dlp is not installed, falling back to HTML metadata extraction")
        return _extract_from_html(url)

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": not download,
    }
    if download:
        os.makedirs(output_dir, exist_ok=True)
        ydl_opts["outtmpl"] = os.path.join(output_dir, "%(extractor)s-%(id)s.%(ext)s")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=download)
            downloaded_file = ""
            if download:
                requested = info.get("requested_downloads") or []
                if requested:
                    downloaded_file = requested[0].get("filepath") or ""
                downloaded_file = downloaded_file or ydl.prepare_filename(info)
            return _normalize_info(url, info, downloaded_file)
    except Exception as exc:
        logger.warning(f"yt-dlp failed to extract Douyin/TikTok link: {exc}")
        try:
            metadata = _extract_from_html(url)
        except Exception:
            raise ValueError(
                "链接解析失败。请确认视频是公开内容；如果抖音要求登录或风控拦截，需要换公开分享链接或后续接入 cookie。"
            ) from exc
        metadata["warning"] = f"yt-dlp 解析失败，已降级为网页元数据解析: {exc}"
        return metadata
