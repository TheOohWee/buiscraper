import re
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor
from functools import reduce

import requests
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/Special:Random"
HEADERS = {"User-Agent": "nd-cse-extra-credit-scraper (atomashp@nd.edu)"}


def fetch(_):
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return ""


def clean(text):
    no_citations = re.sub(r"\[\w+\]", "", text)
    return " ".join(no_citations.split())


def first_text(tags):
    texts = map(lambda tag: tag.get_text().strip(), tags)
    return next(filter(None, texts), "")


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1", id="firstHeading")
    paragraphs = soup.select("div.mw-parser-output p")
    return {
        "title": title.get_text().strip() if title else "?",
        "intro": clean(first_text(paragraphs)),
    }


def scrape(n, workers):
    if workers == 1:
        pages = list(map(fetch, range(n)))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            pages = list(executor.map(fetch, range(n)))
    return list(map(parse, filter(None, pages)))


def timed_scrape(n, workers):
    start = time.perf_counter()
    articles = scrape(n, workers)
    return articles, time.perf_counter() - start


def longest_title(a, b):
    return a if len(a["title"]) >= len(b["title"]) else b


def show(numbered):
    number, article = numbered
    intro = textwrap.shorten(article["intro"], width=100, placeholder="...")
    print(f"{number:>2}. {article['title']}")
    print(f"    {intro}\n")


def main():
    arguments = sys.argv[1:]
    number, workers, compare = 30, 8, False

    while arguments:
        flag = arguments.pop(0)
        if flag == "-n":
            number = int(arguments.pop(0))
        elif flag == "-w":
            workers = int(arguments.pop(0))
        elif flag == "-c":
            compare = True
        else:
            print(f"Usage: {sys.argv[0]} [-n NUMBER] [-w WORKERS] [-c]")
            sys.exit(1)

    runs = (1, workers) if compare else (workers,)
    results = [timed_scrape(number, w) for w in runs]
    articles = results[-1][0]

    list(map(show, enumerate(articles, 1)))
    print(f"Longest title: {reduce(longest_title, articles)['title']}\n")

    for w, (found, seconds) in zip(runs, results):
        print(f"{w} worker(s): {len(found)} articles in {seconds:.2f}s")
    if compare:
        print(f"Speedup: {results[0][1] / results[-1][1]:.1f}x")


if __name__ == "__main__":
    main()
