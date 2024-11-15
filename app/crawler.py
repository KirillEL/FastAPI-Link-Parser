import asyncio
from collections import defaultdict
from urllib.parse import urlparse, urlunparse, urljoin

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import select, or_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import WordList, UrlList, WordLocation, LinkBetweenUrl, LinkWord, MatchRows
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
            words = re.findall(r'\b\w+\b', page_text.lower())  # Извлечение слов

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
    """
    Заполняет таблицу MatchRows, находя URL и соответствующие локации для двух слов.
    """

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

    # Находим все URL и локации для второго слова
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

    # Коммитим изменения в базе данных
    await db.commit()

    print("MatchRows table populated successfully.")
