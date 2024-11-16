import asyncio
from collections import defaultdict
from urllib.parse import urlparse, urlunparse, urljoin

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import select, or_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import WordList, UrlList, WordLocation, LinkBetweenUrl, LinkWord, MatchRows, Metrics
import re

from app.redis import redis_service

STOP_WORDS = {"и", "но", "на", "за", "в", "с", "о", "к", "по", "для", "от"}
processed_urls = set()


def is_absolute_url(url: str) -> bool:
    return bool(urlparse(url).netloc)


def normalize_url(url: str, base_url: str = None) -> str:
    if url.startswith("//"):
        url = "https:" + url

    parsed_url = urlparse(url)
    normalized_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path.rstrip('/'),
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))

    if base_url and not is_absolute_url(normalized_url):
        normalized_url = urljoin(base_url, normalized_url)

    return normalized_url


async def get_words(
        session: aiohttp.ClientSession,
        url: str
) -> list[tuple[str, int]]:
    print("START GET WORDS")
    async with session.get(url, headers={'User-Agent': 'Mozilla/5'}) as response:
        if response.status == 200:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            page_text = soup.get_text(separator=' ')

            words = re.findall(r'\b[a-zA-Zа-яА-Я]+\b', page_text.lower())

            clean_words_with_positions = [(word, idx) for idx, word in enumerate(words) if word not in STOP_WORDS]
            print("END GET WORDS")
            return clean_words_with_positions


async def get_links(
        session: aiohttp.ClientSession,
        url: str
) -> list[str]:
    print("START GET LINKS")
    async with session.get(url, headers={'User-Agent': 'Mozilla/5'}) as response:
        if response.status == 200:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            links = {}
            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']
                if not is_absolute_url(link):
                    link = urljoin(url, link)

                normalized_link = normalize_url(link, url)

                if is_absolute_url(normalized_link) and normalized_link not in links:
                    links[normalized_link] = None
            print("END GET LINKS")
            return list(links.keys())


async def store_words(
        words: list[tuple[str, int]],
        url_id: int,
        db: AsyncSession
) -> None:
    print("START STORE WORDS")
    for word, position in words:
        word_model = WordList(word=word)
        db.add(word_model)
        await db.flush()

        word_location = WordLocation(fk_word_id=word_model.id, fk_url_id=url_id, location=position)
        db.add(word_location)

        link_word = LinkWord(fk_word_id=word_model.id, fk_link_id=url_id)
        db.add(link_word)

    await db.commit()
    print("END STORE WORDS")


async def store_links(
        links: list[str],
        from_url_id: int,
        db: AsyncSession
) -> None:
    print("START STORE LINKS")
    for link in links:
        stmt = select(UrlList).where(UrlList.url == link)
        result = await db.execute(stmt)
        link_model = result.scalars().first()

        if not link_model:
            link_model = UrlList(url=link)
            db.add(link_model)
            await db.flush()

        link_between = LinkBetweenUrl(
            fk_fromurl_id=from_url_id,
            fk_tourl_id=link_model.id
        )
        db.add(link_between)

    await db.commit()
    print("END STORE LINKS")


async def crawl(
        url: str,
        db: AsyncSession,
        session: aiohttp.ClientSession,
        depth: int = 0
):
    if depth >= 10:
        return
    print(f"START CRAWLING URL: {url}")

    normalized_url = normalize_url(url)

    res = await redis_service.is_url_cached(normalized_url)
    if res:
        print(f"URL {normalized_url} уже обработан, пропускаем.")
        return

    await redis_service.cache_url(normalized_url)

    stmt = select(UrlList).where(UrlList.url == normalized_url)
    result = await db.execute(stmt)
    url_model = result.scalars().first()

    if not url_model:
        url_model = UrlList(url=normalized_url)
        db.add(url_model)
        await db.flush()

    links = await get_links(session, url)
    words = await get_words(session, url)

    if links is None:
        print(f"ON URL: {url} NOT FOUND LINKS!")
        return

    await store_links(links, url_model.id, db)
    await store_words(words, url_model.id, db)

    if links:
        for link in links:
            await crawl(link, db, session, depth=depth + 1)
    else:
        print("NO LINKS")


async def populate_matchrows(word1: str, word2: str, db: AsyncSession):
    stmt1 = (
        select(
            WordLocation.fk_url_id.label("url_id"),
            WordLocation.location.label("location"),
        )
        .join(WordList, WordList.id == WordLocation.fk_word_id)
        .where(WordList.word == word1)
    )
    result1 = await db.execute(stmt1)
    rows1 = result1.fetchall()
    print(f"rows1: {rows1}")

    stmt2 = (
        select(
            WordLocation.fk_url_id.label("url_id"),
            WordLocation.location.label("location"),
        )
        .join(WordList, WordList.id == WordLocation.fk_word_id)
        .where(WordList.word == word2)
    )
    result2 = await db.execute(stmt2)
    rows2 = result2.fetchall()
    print(f"rows2: {rows2}")

    word1_locations = defaultdict(list)
    for row in rows1:
        word1_locations[row.url_id].append(row.location)

    word2_locations = defaultdict(list)
    for row in rows2:
        word2_locations[row.url_id].append(row.location)

    common_url_ids = set(word1_locations.keys()) & set(word2_locations.keys())

    for url_id in common_url_ids:
        for loc1 in word1_locations[url_id]:
            for loc2 in word2_locations[url_id]:
                match_row = MatchRows(
                    url_id=url_id,
                    loc_word1=loc1,
                    loc_word2=loc2,
                )
                db.add(match_row)

    await db.commit()

    print("MatchRows table populated successfully.")




async def calc_metrics(db: AsyncSession, damping_factor=0.85, iterations=20):
    freq_stmt = (
        select(
            MatchRows.url_id.label("url_id"),
            (
                func.count(func.distinct(MatchRows.loc_word1)) +
                func.count(func.distinct(MatchRows.loc_word2))
            ).label("metric_freq")
        )
        .group_by(MatchRows.url_id)
    )
    freq_result = await db.execute(freq_stmt)
    frequency_data = freq_result.fetchall()

    urls_stmt = select(LinkBetweenUrl.fk_fromurl_id).union(
        select(LinkBetweenUrl.fk_tourl_id)
    )
    urls_result = await db.execute(urls_stmt)
    urls = [row[0] for row in urls_result.fetchall()]

    num_urls = len(urls)
    pagerank = {url: 1 / num_urls for url in urls}

    links_stmt = (
        select(LinkBetweenUrl.fk_fromurl_id, LinkBetweenUrl.fk_tourl_id)
    )
    links_result = await db.execute(links_stmt)
    links = links_result.fetchall()

    outgoing_links = {}
    for from_url, to_url in links:
        outgoing_links.setdefault(from_url, []).append(to_url)

    for _ in range(iterations):
        new_pagerank = {url: (1 - damping_factor) / num_urls for url in urls}
        for from_url, to_urls in outgoing_links.items():
            share = pagerank[from_url] / len(to_urls)
            for to_url in to_urls:
                if to_url in new_pagerank:
                    new_pagerank[to_url] += damping_factor * share
        pagerank = new_pagerank

    max_pr = max(pagerank.values(), default=0)
    min_pr = min(pagerank.values(), default=0)

    if max_pr != min_pr:
        normalized_pagerank = {
            url: (pr - min_pr) / (max_pr - min_pr)
            for url, pr in pagerank.items()
        }
    else:
        normalized_pagerank = {url: 0 for url in pagerank.keys()}

    metrics = {}
    for row in frequency_data:
        metrics[row.url_id] = {"metric_freq": row.metric_freq}

    for url_id, pr in pagerank.items():
        if url_id in metrics:
            metrics[url_id]["metric_pagerank"] = pr
            metrics[url_id]["normal_metric_pagerank"] = normalized_pagerank[url_id]

    freq_values = [data["metric_freq"] for data in metrics.values()]
    freq_min, freq_max = min(freq_values), max(freq_values)

    for url_id, data in metrics.items():
        data["normal_metric_freq"] = (
            (data["metric_freq"] - freq_min) / (freq_max - freq_min) if freq_max != freq_min else 1
        )
        data["result_metric"] = (data["normal_metric_freq"] + data["normal_metric_pagerank"]) / 2

    for url_id, data in metrics.items():
        db.add(Metrics(
            url_id=url_id,
            metric_freq=data["metric_freq"],
            metric_pagerank=data["metric_pagerank"],
            normal_metric_freq=data["normal_metric_freq"],
            normal_metric_pagerank=data["normal_metric_pagerank"],
            result_metric=data["result_metric"]
        ))

    await db.commit()


async def get_sorted_metrics(db: AsyncSession):
    stmt = (
        select(
            Metrics.url_id,
            Metrics.result_metric
        )
        .order_by(Metrics.result_metric.desc())
    )
    result = await db.execute(stmt)
    return result.fetchall()


async def fetch_text_from_url(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    return soup.get_text()
                else:
                    return f"Ошибка загрузки текста: {response.status}"
        except Exception as e:
            return f"Ошибка при подключении: {str(e)}"


def highlight_words(text, words):
    for word in words:
        regex = re.compile(re.escape(word), re.IGNORECASE)
        text = regex.sub(f'<span class="highlight">{word}</span>', text)
    return text


async def generate_html_report(db: AsyncSession, output_file="report.html"):
    sorted_metrics = await get_sorted_metrics(db)
    words_to_highlight = ["деятельность", "редактора"]

    html_content = "<html><head><style>.highlight { background-color: yellow; font-weight: bold; }</style></head><body>"
    html_content += "<h1>URL Report</h1>"

    for url_id, result_metric in sorted_metrics:
        stmt = select(UrlList.url).where(UrlList.id == url_id)
        result = await db.execute(stmt)
        url = result.scalar()


        text = await fetch_text_from_url(url)

        highlighted_text = highlight_words(text, words_to_highlight)

        html_content += f"<h2>URL: {url} (Metric: {result_metric})</h2>"
        html_content += f"<div>{highlighted_text}</div>"

    html_content += "</body></html>"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML report generated: {output_file}")
