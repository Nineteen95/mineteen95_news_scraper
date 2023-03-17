import asyncio
from typing import List, Tuple
import random

import newspaper
from newspaper import Article
from newspaper.article import ArticleException

from nlp import summarize_text
from proxy import get_proxy


async def scrape_news_article(url: str) -> Tuple[str, str, str]:
    """
    Scrape a news article from a given URL and return a tuple containing the URL, the article title,
    and a summary of the article.
    """
    try:
        # Use newspaper3k to scrape the article
        article = Article(url)
        article.download()
        article.parse()

        # Summarize the article using NLP
        summary = summarize_text(article.text)

        return url, article.title, summary

    except ArticleException as e:
        print(f"Error scraping article at {url}: {e}")
        return None


async def scrape_news_sources(news_sources: List[str], num_articles_per_source: int = 3) -> List[Tuple[str, str, str]]:
    """
    Scrape news articles from a list of news sources.
    """
    # Retrieve a list of available proxies
    proxies = await get_proxy()

    # Shuffle the news sources to spread out the load on different domains
    random.shuffle(news_sources)

    # Use newspaper3k to retrieve and parse news articles
    news_articles = []
    for source_url in news_sources:
        try:
            source = newspaper.build(source_url, memoize_articles=False)
        except Exception as e:
            print(f"Error building source at {source_url}: {e}")
            continue

        # Shuffle the articles to spread out the load on different domains
        random.shuffle(source.articles)

        for article in source.articles[:num_articles_per_source]:
            # Choose a random proxy from the list of available proxies
            proxy = random.choice(proxies) if proxies else None

            try:
                # Use newspaper3k to parse the article
                article.download(proxy=proxy)
                article.parse()

                # Check if the article already exists in the database
                if ArticleModel.get_by_url(article.url):
                    print(f"Skipping already saved article: {article.url}")
                    continue

                # Summarize the article using NLP
                summary = summarize_text(article.text)

                # Save the article to the database
                ArticleModel.create(url=article.url, title=article.title, summary=summary)

                # Add the article to the list of news articles
                news_articles.append((article.url, article.title, summary))

            except ArticleException as e:
                print(f"Error scraping article at {article.url}: {e}")
                continue

            except Exception as e:
                print(f"Error saving article at {article.url}: {e}")
                continue

    return news_articles
