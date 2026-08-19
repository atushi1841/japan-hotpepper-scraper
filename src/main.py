import asyncio
import json
import re
import sys

import httpx
try:
    from apify import Actor
except Exception:
    Actor = None


# 都道府県コード（ホットペッパー公式URLパス・実サイト確認 2026-08-19）
AREA_CODES = {
    "hokkaido": "SA41", "aomori": "SA51", "akita": "SA54", "yamagata": "SA55",
    "iwate": "SA52", "miyagi": "SA53", "fukushima": "SA56",
    "tokyo": "SA11", "kanagawa": "SA12", "saitama": "SA13", "chiba": "SA14",
    "tochigi": "SA16", "ibaraki": "SA15", "gunma": "SA17",
    "niigata": "SA61", "yamanashi": "SA65", "nagano": "SA66",
    "ishikawa": "SA63", "toyama": "SA62", "fukui": "SA64",
    "aichi": "SA33", "gifu": "SA31", "shizuoka": "SA32", "mie": "SA34",
    "osaka": "SA23", "hyogo": "SA24", "kyoto": "SA22", "nara": "SA25",
    "wakayama": "SA26", "shiga": "SA21",
    "okayama": "SA73", "hiroshima": "SA74", "tottori": "SA71", "shimane": "SA72",
    "yamaguchi": "SA75", "kagawa": "SA82", "ehime": "SA83", "tokushima": "SA81",
    "kochi": "SA84", "fukuoka": "SA91", "saga": "SA92", "nagasaki": "SA93",
    "kumamoto": "SA94", "oita": "SA95", "miyazaki": "SA96", "kagoshima": "SA97",
    "okinawa": "SA98",
}

# 主要ジャンルコード
GENRE_CODES = {
    "izakaya": "G001", "diningbar": "G002", "creative": "G003",
    "washoku": "G004", "yoshoku": "G005", "chuuka": "G007",
    "asian": "G009", "bar": "G012", "ramen": "G013",
    "okonomiyaki": "G016",
}

GENRE_LABELS = {
    "G001": "居酒屋", "G002": "ダイニングバー・バル", "G003": "創作料理",
    "G004": "和食", "G005": "洋食", "G007": "中華", "G009": "アジア・エスニック",
    "G012": "バー・カクテル", "G013": "ラーメン", "G016": "お好み焼き・もんじゃ",
}


def _clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


async def fetch_page(client, url):
    resp = await client.get(url)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_listing(html, area_code, genre_code):
    """一覧ページから店舗カードを抽出."""
    shops = []
    # 各店舗カードのブロック（shopDetailTop が1店舗）
    blocks = re.split(r'<div class="shopDetailTop', html)
    for block in blocks[1:]:
        if "strJ" not in block or "<h3" not in block:
            continue
        m_url = re.search(r'href="(/strJ\d+/)"', block)
        if not m_url:
            continue
        url = "https://www.hotpepper.jp" + m_url.group(1)
        shop_id = m_url.group(1).split("str")[1].rstrip("/")

        m_name = re.search(r'<h3 class="shopDetailStoreName">\s*<a[^>]*>(.*?)</a>', block, re.S)
        name = _clean(re.sub(r"<[^>]+>", "", m_name.group(1))) if m_name else None

        m_genre = re.search(r'<p class="parentGenreName">(.*?)</p>', block, re.S)
        genre_label = _clean(m_genre.group(1)) if m_genre else None

        m_catch = re.search(r'<p class="shopDetailGenreCatch[^"]*">(.*?)</p>', block, re.S)
        catch = _clean(re.sub(r"<[^>]+>", "", m_catch.group(1))) if m_catch else None

        m_dinner = re.search(r'<p class="dinnerBudget">(.*?)</p>', block, re.S)
        dinner_budget = _clean(m_dinner.group(1)) if m_dinner else None
        m_lunch = re.search(r'<p class="lunchBudget">(.*?)</p>', block, re.S)
        lunch_budget = _clean(m_lunch.group(1)) if m_lunch else None

        m_access = re.search(r'<li class="shopDetailInfoAccess"[^>]*>(.*?)</li>', block, re.S)
        access = _clean(re.sub(r"<[^>]+>", "", m_access.group(1))) if m_access else None

        m_img = re.search(r'<img src="(https://imgfp\.hotp\.jp/[^"]+)" alt="', block)
        image_url = m_img.group(1) if m_img else None

        # 【PR】判定
        is_pr = "【PR】" in block

        # ラテロン
        m_lat = re.search(r'data-lat="([\d.]+)"', block)
        m_lon = re.search(r'data-lon="([\d.]+)"', block)
        lat = m_lat.group(1) if m_lat else None
        lon = m_lon.group(1) if m_lon else None

        if not name:
            continue
        shops.append({
            "shopId": shop_id,
            "name": name,
            "url": url,
            "genre": genre_label,
            "genreCode": genre_code,
            "catchphrase": catch,
            "dinnerBudget": dinner_budget,
            "lunchBudget": lunch_budget,
            "access": access,
            "areaCode": area_code,
            "imageUrl": image_url,
            "lat": lat,
            "lon": lon,
            "isSponsored": is_pr,
        })
    return shops


async def run(actor_input, actor=None):
    area_key = actor_input.get("area") or "tokyo"
    genre_key = actor_input.get("genre") or "izakaya"
    max_items = int(actor_input.get("maxItems", 100))
    max_pages = int(actor_input.get("maxPages", 5))

    # コード解決（ラテン名・コード・本人入力のいずれにも対応）
    def resolve_code(key, mapping):
        # 都道府県/ジャンルのラテン名 → コード
        if key in mapping:
            return mapping[key]
        # 既にコード（SA11 / G001）ならそのまま
        if key.upper() in mapping.values():
            return key.upper()
        return key

    area_code = resolve_code(area_key.lower(), AREA_CODES)
    genre_code = resolve_code(genre_key.lower(), GENRE_CODES)

    proxy_url = None
    if actor is not None:
        proxy_config = await actor.create_proxy_configuration(actor_proxy_input=actor_input.get("proxyConfiguration"))
        if proxy_config:
            proxy_url = await proxy_config.new_url()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    base = f"https://www.hotpepper.jp/{area_code}/{genre_code}/"
    collected = 0

    async with httpx.AsyncClient(proxy=proxy_url, headers=headers, timeout=30.0, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            if collected >= max_items:
                break
            url = base if page == 1 else f"{base}bgn{page}/"
            try:
                html = await fetch_page(client, url)
            except Exception as e:
                if actor is not None:
                    await Actor.log.warning(f"page {page} error: {e}")
                else:
                    print(f"WARN page {page} error: {e}")
                break
            shops = parse_listing(html, area_code, genre_code)
            if not shops:
                break
            for shop in shops:
                if collected >= max_items:
                    break
                genre_label = shop["genre"] or GENRE_LABELS.get(genre_code, "")
                item = {
                    "shopId": shop["shopId"],
                    "name": shop["name"],
                    "genre": genre_label,
                    "genreCode": genre_code,
                    "catchphrase": shop["catchphrase"],
                    "dinnerBudget": shop["dinnerBudget"],
                    "lunchBudget": shop["lunchBudget"],
                    "access": shop["access"],
                    "area": area_code,
                    "url": shop["url"],
                    "imageUrl": shop["imageUrl"],
                    "lat": shop["lat"],
                    "lon": shop["lon"],
                    "isSponsored": shop["isSponsored"],
                }
                if actor is not None:
                    await Actor.push_data(item)
                else:
                    print(json.dumps(item, ensure_ascii=False))
                collected += 1
            if actor is not None:
                await Actor.log.info(f"page {page}: collected {collected}/{max_items} ({len(shops)} cards)")
            else:
                print(f"DEBUG page {page}: collected {collected}/{max_items} ({len(shops)} cards)")


async def main():
    actor_input = {}
    if Actor is not None and Actor.is_at_home():
        async with Actor:
            actor_input = await Actor.get_input() or {}
            await run(actor_input, actor=Actor)
    else:
        raw = sys.stdin.read().strip()
        if raw:
            actor_input = json.loads(raw)
        await run(actor_input, actor=None)


if __name__ == "__main__":
    asyncio.run(main())
