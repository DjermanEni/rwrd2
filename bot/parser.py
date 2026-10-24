"""Парсинг форума: список тем раздела, анкета персонажа, аватары."""

import re
import time
import requests
from bs4 import BeautifulSoup

from bot.config import (
    FORUM_URL, FORUM_ID, MAX_PAGES, REQUEST_TIMEOUT, REQUEST_DELAY, logger
)
from bot.forum_session import forum_session


def get_forum_topics():
    """Собирает список тем из раздела FORUM_ID со всех страниц (до MAX_PAGES)."""
    topics = []
    page = 1
    while page <= MAX_PAGES:
        url = f"{FORUM_URL}/viewforum.php?id={FORUM_ID}"
        if page > 1:
            url += f"&p={page}"
        logger.info(f"Загрузка страницы {page}: {url}")
        try:
            response = forum_session().get(url, headers={"Referer": f"{FORUM_URL}/index.php"}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Ошибка загрузки страницы {page}: {e}")
            break
        soup = BeautifulSoup(response.text, "html.parser")
        topic_table = soup.find("table", attrs={"summary": re.compile(r"Список тем")})
        if not topic_table:
            forum_div = soup.find("div", class_="forum")
            if forum_div:
                topic_table = forum_div.find("table")
        if not topic_table:
            # запасной вариант: собираем ссылки на темы прямо со страницы
            all_links = soup.find_all("a", href=re.compile(r"viewtopic\.php\?id=\d+"))
            for link in all_links:
                href = link.get("href", "")
                if "#p" in href:
                    continue
                m = re.search(r"id=(\d+)", href)
                if m:
                    tid = m.group(1)
                    title = link.get_text(strip=True)
                    if len(title) < 3:
                        continue
                    ym = re.search(r'\[(\d{4}(?:\s*/\s*\d{4})?)\]', title)
                    year = ym.group(1) if ym else ""
                    tc = re.sub(r'^\[\d{4}(?:\s*/\s*\d{4})?\]\s*', '', title)
                    tc = re.sub(r'\s*\[\d{4}(?:\s*/\s*\d{4})?\]$', '', tc)
                    if any(t["id"] == tid for t in topics):
                        continue
                    topics.append({"id": tid, "title": tc, "title_full": title, "author": "Unknown", "year": year, "url": f"{FORUM_URL}/viewtopic.php?id={tid}"})
            break
        rows = topic_table.find_all("tr")
        found = False
        for row in rows:
            link = row.find("a", href=re.compile(r"viewtopic\.php\?id=\d+"))
            if not link:
                continue
            href = link.get("href", "")
            if "#p" in href:
                continue
            m = re.search(r"id=(\d+)", href)
            if not m:
                continue
            tid = m.group(1)
            title = link.get_text(strip=True)
            if len(title) < 3:
                continue
            au = row.find("span", class_="byuser-username")
            author = au.get_text(strip=True) if au else "Unknown"
            ym = re.search(r'\[(\d{4}(?:\s*/\s*\d{4})?)\]', title)
            year = ym.group(1) if ym else ""
            tc = re.sub(r'^\[\d{4}(?:\s*/\s*\d{4})?\]\s*', '', title)
            tc = re.sub(r'\s*\[\d{4}(?:\s*/\s*\d{4})?\]$', '', tc)
            topics.append({"id": tid, "title": tc, "title_full": title, "author": author, "year": year, "url": f"{FORUM_URL}/viewtopic.php?id={tid}"})
            found = True
        if not found:
            break
        if not soup.find("a", class_="next"):
            break
        time.sleep(REQUEST_DELAY)
        page += 1
    logger.info(f"Всего найдено тем: {len(topics)}")
    return topics


def parse_character_sheet(topic_url):
    """Извлекает поля анкеты персонажа из первого поста темы."""
    try:
        response = forum_session().get(topic_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка загрузки темы {topic_url}: {e}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    pc = soup.find("div", class_="post-content")
    if not pc:
        pc = soup.find("div", class_="postmsg")
    if not pc:
        pc = soup.find("div", class_="blockpost")
    if not pc:
        return None
    ch = {}
    pt = pc.get_text(separator="\n", strip=True)

    # Имя
    nt = pc.find("div", class_="custom_tag_name")
    if nt:
        ch["name"] = nt.get_text(strip=True)
    else:
        for line in pt.split("\n")[:10]:
            line = line.strip()
            if line and 2 < len(line) < 50 and not line.startswith(("http", "Автор:", "Участник", "Новичок", "Активный")):
                if any(s in line for s in ["Сообщений", "Уважение", "Провел на форуме", "Последний визит", "Активен", "2077", "2099"]):
                    continue
                ch["name"] = line
                break

    # Позывной
    mt = pc.find("div", class_="custom_tag_moniker")
    if mt:
        ch["moniker"] = mt.get_text(strip=True)

    # Дата рождения
    dt = pc.find("div", class_="custom_tag_dob")
    if dt:
        ch["dob"] = dt.get_text(strip=True)
    else:
        dm = re.search(r'(\d{2}\.\d{2}\.\d{4})', pt)
        if dm:
            ch["dob"] = dm.group(1)

    # Занятие / лояльность
    ot = pc.find("div", class_="custom_tag_occupation")
    if ot:
        ch["occupation"] = ot.get_text(strip=True)
    lt = pc.find("div", class_="custom_tag_loyalty")
    if lt:
        ch["loyalty"] = lt.get_text(strip=True)

    # Импланты / навыки
    i1 = pc.find("div", class_="custom_tag_info1")
    if i1:
        implants = []
        for li in i1.find_all("li"):
            t = li.get_text(strip=True)
            if t and not t.endswith(":") and len(t) > 1:
                implants.append(t)
        ch["implants"] = implants
    i2 = pc.find("div", class_="custom_tag_info2")
    if i2:
        skills = []
        for li in i2.find_all("li"):
            t = li.get_text(strip=True)
            if t:
                skills.append(t)
        ch["skills"] = skills

    # Биография
    at = pc.find("div", class_="custom_tag_anktxt")
    if at:
        for q in at.find_all(["div"], class_=re.compile(r"quote-box|spoiler-box")):
            q.decompose()
        # Удаляем встроенные стили/скрипты и BBCode-разметку [html]...[/html],
        # иначе их текст попадает в сообщение бота как мусор
        for tag in at.find_all(["style", "script"]):
            tag.decompose()
        bio_html = str(at)
        bio_html = re.sub(r"\[/?html\]", "", bio_html)
        clean_soup = BeautifulSoup(bio_html, "html.parser")
        ch["bio"] = clean_soup.get_text(separator="\n", strip=True)
    else:
        for q in pc.find_all("blockquote"):
            q.decompose()
        bio = pc.get_text(separator="\n", strip=True)
        bl = []
        for line in bio.split("\n"):
            if any(s in line for s in ["ДОПОЛНИТЕЛЬНО", "ПРИМЕР ПОСТА", "свернуть блок"]):
                break
            bl.append(line)
        bio = "\n".join(bl).strip()
        if len(bio) > 200:
            ch["bio"] = bio

    # Таймлайн
    yt = pc.find("lzyear")
    if yt:
        ch["year"] = yt.get_text(strip=True)

    # Аватар автора первого поста (парсим из всей страницы, т.к. аватар вне post-content)
    avatar_url = extract_avatar_url(soup)
    if avatar_url:
        ch["avatar_url"] = avatar_url
    return ch


def extract_avatar_url(soup):
    """Ищет URL аватара автора первого поста темы.

    На rwrd.rusff.me аватар — это <img> с домена forumavatars.ru внутри
    контейнера первого поста (div.post), рядом со ссылкой на профиль автора.
    """
    first_post = soup.find("div", class_=re.compile(r"\bpost\b"))
    scope = first_post if first_post else soup
    for img in scope.find_all("img"):
        src = img.get("src", "") or ""
        cls = " ".join(img.get("class") or [])
        if "postimg" in cls:  # картинки в самом тексте анкеты пропускаем
            continue
        if "forumavatars" in src:
            return src
    # запасной вариант: любой avatar-хостинг форума вне текста поста
    m = re.search(r'https?://forumavatars\.ru/[^"\'<> ]+\.(?:png|jpe?g|gif)', str(first_post or soup))
    return m.group(0) if m else None


def download_avatar(avatar_url):
    """Скачивает аватар, возвращает bytes или None (если не картинка/недоступен)."""
    if not avatar_url:
        return None
    try:
        r = forum_session().get(avatar_url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if "image" not in ctype or len(r.content) < 100:
            logger.info(f"Аватар недоступен или не картинка: {avatar_url} ({ctype})")
            return None
        if len(r.content) > 5 * 1024 * 1024:  # Telegram лимит — 5 МБ
            return None
        return r.content
    except requests.RequestException as e:
        logger.warning(f"Не удалось скачать аватар {avatar_url}: {e}")
        return None


def get_active_topics():
    """Парсит страницу https://rwrd.rusff.me/search.php?action=show_recent
    (список последних активных тем форума)."""
    url = f"{FORUM_URL}/search.php?action=show_recent"
    logger.info(f"Загрузка активных тем: {url}")
    try:
        response = forum_session().get(url, headers={"Referer": f"{FORUM_URL}/index.php"}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка загрузки активных тем: {e}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    topic_table = soup.find("table", attrs={"summary": re.compile(r"Результаты поиска")})
    if not topic_table:
        # запасной вариант: последняя таблица на странице (обычно и есть результат)
        tables = soup.find_all("table")
        topic_table = tables[-1] if tables else None
    if not topic_table:
        logger.warning("Таблица активных тем не найдена")
        return []
    topics = []
    for row in topic_table.find_all("tr"):
        tcl = row.find("td", class_="tcl")
        if not tcl:
            continue  # строка заголовков или мусор
        # Название темы — первая ссылка на viewtopic без пагинации (&p=) и якорей (#p)
        topic_link = None
        for a in tcl.find_all("a", href=re.compile(r"viewtopic\.php\?id=\d+")):
            h = a.get("href", "")
            if "#p" in h or "&p=" in h or "?p=" in h:
                continue
            topic_link = a
            break
        if not topic_link:
            continue
        topic_title = topic_link.get_text(strip=True)
        topic_url = topic_link.get("href", "")
        if not topic_title:
            continue
        # Форум, к которому относится тема (колонка "Форум")
        tc2 = row.find("td", class_="tc2")
        forum_name = tc2.get_text(strip=True) if tc2 else ""
        # Количество ответов (колонка "Ответов")
        tc3 = row.find("td", class_="tc3")
        replies = tc3.get_text(strip=True) if tc3 else ""
        # Последнее сообщение: время (ссылка с якорем #p), автор (ссылка на profile.php)
        last_author = ""
        last_post_url = topic_url
        last_post_time = ""
        tcr = row.find("td", class_="tcr")
        if tcr:
            plink = tcr.find("a", href=re.compile(r"#p\d+"))
            if plink:
                last_post_url = plink.get("href", topic_url)
                last_post_time = plink.get_text(strip=True)
            au = tcr.find("span", class_="byuser-username")
            if not au:
                # запасной вариант: имя автора в ссылке на профиль (мимо аватара)
                for a in tcr.find_all("a", href=re.compile(r"profile\.php")):
                    txt = a.get_text(strip=True)
                    if txt:
                        au = txt
                        break
            if au:
                last_author = au.get_text(strip=True) if hasattr(au, "get_text") else au
        topics.append({
            "title": topic_title,
            "topic_url": topic_url,
            "forum": forum_name,
            "replies": replies,
            "last_post_url": last_post_url,
            "last_post_time": last_post_time,
            "last_author": last_author,
        })
    logger.info(f"Найдено активных тем: {len(topics)}")
    return topics
