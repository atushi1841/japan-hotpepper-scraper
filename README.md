# Japan HotPepper Gourmet Restaurants Scraper

Scrape Japanese restaurant listings from **HOT PEPPER Gourmet (ホットペッパーグルメ)**, one of Japan's largest restaurant reservation and coupon portals (operated by Recruit). This Actor extracts restaurants by prefecture and food genre, including name, cuisine type, catchphrase, dinner/lunch budget, nearest station & access, exact GPS coordinates, and whether the listing is sponsored.

Perfect for **Japan food market research**, **restaurant lead generation**, **travel & tourism analytics**, **menu/budget analysis**, and **regional cuisine studies**.

## Output Sample

```json
{
  "shopId": "J004660516",
  "name": "もつ焼き ひふみ屋",
  "genre": "居酒屋｜道玄坂",
  "genreCode": "G001",
  "catchphrase": "厳選もつ焼きが自慢！大人のグルメな隠れ家",
  "dinnerBudget": "4001～5000円",
  "lunchBudget": null,
  "access": "各線【渋谷駅】A2出口より徒歩4分...",
  "area": "SA11",
  "url": "https://www.hotpepper.jp/strJ004660516/",
  "imageUrl": "https://imgfp.hotp.jp/IMGH/57/61/P051005761/P051005761_238.jpg",
  "lat": "35.6602652",
  "lon": "139.6971312",
  "isSponsored": false
}
```

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `area` | string | `tokyo` | Prefecture. Keyword (`tokyo`, `osaka`, `hokkaido`, `kanagawa`...) or code (`SA11`=Tokyo, `SA23`=Osaka, `SA91`=Fukuoka...) |
| `genre` | string | `izakaya` | Food genre. Keyword (`izakaya`, `ramen`, `yoshoku`...) or code (`G001`=Izakaya, `G013`=Ramen...) |
| `maxItems` | integer | 100 | Max restaurants to collect |
| `maxPages` | integer | 5 | Max listing pages to crawl (1 page ≈ 20 restaurants) |
| `proxyConfiguration` | object | auto | Apify proxy (recommended for large runs) |

### Area codes (all 47 prefectures)

`tokyo`=SA11, `kanagawa`=SA12, `osaka`=SA23, `kyoto`=SA22, `aichi`=SA33, `hokkaido`=SA41, `fukuoka`=SA91, `chiba`=SA14, `saitama`=SA13, `hyogo`=SA24, `hiroshima`=SA74, `okinawa`=SA98, and all others.

### Genre codes

`izakaya`(居酒屋)=G001, `diningbar`(ダイニングバー・バル)=G002, `creative`(創作料理)=G003, `washoku`(和食)=G004, `yoshoku`(洋食)=G005, `chuuka`(中華)=G007, `asian`(アジア・エスニック)=G009, `bar`(バー・カクテル)=G012, `ramen`(ラーメン)=G013, `okonomiyaki`(お好み焼き・もんじゃ)=G016.

## Use Cases

- **Market research**: Compare restaurant density, cuisine mix, and price ranges across Japanese prefectures
- **Lead generation**: Build regional restaurant databases for B2B outreach (suppliers, SaaS, delivery platforms)
- **Travel analytics**: Map dining options and budgets for tourism planning
- **Academic studies**: Analyze Japan's food service industry by region and category
- **Price monitoring**: Track budget range distributions over time

## Limitations

- Data is limited to what HotPepper Gourmet publicly displays; not all Japanese restaurants are listed
- Reviews/scores are not part of the listing HTML (HotPepper uses a reservation model, not ratings)
- `dinnerBudget` / `lunchBudget` may be `null` when the restaurant doesn't display a budget
- Listings marked `isSponsored: true` are PR placements (paid)
