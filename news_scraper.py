import scrapy
from datetime import datetime
from news.items import NewsItem
import re
import logging
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.log import configure_logging

# Configure logging
configure_logging(install_root_handler=False)
logging.basicConfig(
    filename='news_scraper.log',
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    level=logging.INFO
)

class NewsScraperSpider(scrapy.Spider):
    name = "news_scraper"
    allowed_domains = ["apnews.com", "aljazeera.com", "cnn.com", "bbc.com"]
    start_urls = [
        "https://www.apnews.com/",
        "https://www.aljazeera.com/",
        "https://edition.cnn.com/",
        "https://www.bbc.com/"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_urls = set()

    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'DOWNLOAD_TIMEOUT': 10,
        'RETRY_TIMES': 4,
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'WARNING',
        'DOWNLOAD_DELAY': 4,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'CLOSESPIDER_TIMEOUT': 1800,
        'CLOSESPIDER_PAGECOUNT': 0,
        'RETRY_ENABLED': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 8.0,
        'DNS_TIMEOUT': 20,
        'DEPTH_LIMIT': 12,
    }

    def clean_text(self, text_list):
        if not text_list:
            return None
        text = ' '.join([str(t).strip() for t in text_list if t])
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'<[^>]+>', '', text)
        return text if text else None

    def parse(self, response):
        try:
            self.logger.info(f"Parsing homepage: {response.url}")
            if "apnews.com" in response.url:
                yield from self.parse_apnews(response)
            elif "aljazeera.com" in response.url:
                yield from self.parse_aljazeera(response)
            elif "cnn.com" in response.url:
                yield from self.parse_cnn(response)
            elif "bbc.com" in response.url:
                yield from self.parse_bbc(response)
            else:
                self.logger.warning(f"Unknown domain: {response.url}")
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {str(e)}")

    # -------- AP NEWS --------
    def parse_apnews(self, response):
        try:
            # 1. Crawl category links
            category_links = response.css(
                'a.AnClick-MainNav::attr(href), a.Subheader-Sections-items-item::attr(href), a[data-key="nav-bar-section"]::attr(href), nav[aria-label="Main Navigation"] a::attr(href)'
            ).getall()
            for link in category_links:
                if not link:
                    continue
                if not link.startswith('http'):
                    link = f"https://apnews.com{link}"
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_apnews, dont_filter=True)

            # 2. Crawl article links
            article_links = response.css(
                'a.Link::attr(href), a[data-key="card-headline"]::attr(href), a.headline::attr(href), a.CardHeadline::attr(href), a.story-headline::attr(href), a.related-story-headline::attr(href)'
            ).getall()
            for link in article_links:
                if not link:
                    continue
                if not link.startswith('http'):
                    link = f"https://apnews.com{link}"
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_apnews_article, errback=self.errback_httpbin, dont_filter=True)
        except Exception as e:
            self.logger.error(f"Error in parse_apnews: {str(e)}")

    def parse_apnews_article(self, response):
        try:
            item = NewsItem()
            date_results = response.css(
                'bsp-timestamp span[data-date]::text, bsp-timestamp[data-timestamp] span[data-date]::text, div.Article-datePublished::text, time::attr(datetime), span.timestamp::text, .Timestamp::text'
            ).getall()
            item['date'] = self.clean_text(date_results)
            event_results = response.css(
                'h1.Page-headline::text, span.PagePromoContentIcons::text, h1.Article-headline::text, h1::text, .headline::text, .article-title::text'
            ).getall()
            item['event'] = self.clean_text(event_results)
            item['type'] = "News Article"
            desc_results = response.css(
                'div.RichTextStoryBody.RichTextBody p::text, Span.linkEnhancement a::text, div.Article-content p::text, article p::text, .article-body p::text, .story-body p::text'
            ).getall()
            item['description'] = self.clean_text(desc_results)
            item['source_url'] = response.url
            item['source_name'] = "AP News"
            if item['event'] and item['description']:
                yield item
            else:
                self.logger.warning(f"Skipping blank AP News article: {response.url}")
        except Exception as e:
            self.logger.error(f"Error in parse_apnews_article: {str(e)}")

    # -------- AL JAZEERA --------
    def parse_aljazeera(self, response):
        try:
            # 1. Crawl category links
            category_links = response.css(
                'a::attr(href), nav.menu-navbar a.menu-navbar__link::attr(href), nav.menu-navbar a::attr(href), nav[aria-label="Main Navigation"] a::attr(href)'
            ).getall()
            for link in category_links:
                if not link:
                    continue
                if not link.startswith('http'):
                    link = f"https://www.aljazeera.com{link}"
                if link not in self.visited_urls and (
                    '/news/' in link or '/features/' in link or '/opinions/' in link
                ):
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_aljazeera, dont_filter=True)

            # 2. Crawl article links
            article_links = response.css(
                'a.u-clickable-card__link.article-card__link::attr(href), a.u-clickable-card__link::attr(href), a::attr(href), a.article-trending__title-link.u-clickable-card__link::attr(href), a.liveblog-timeline__update-link::attr(href)'
            ).getall()
            filtered_links = []
            for link in article_links:
                if not link:
                    continue
                if '/news/' in link or '/features/' in link or '/opinions/' in link:
                    if not link.startswith('http'):
                        link = f"https://www.aljazeera.com{link}"
                    if link not in self.visited_urls:
                        filtered_links.append(link)
                        self.visited_urls.add(link)
            for link in filtered_links:
                yield scrapy.Request(
                    link,
                    callback=self.parse_aljazeera_article,
                    errback=self.errback_httpbin,
                    dont_filter=True,
                    meta={'dont_redirect': False, 'handle_httpstatus_list': [301, 302]}
                )
        except Exception as e:
            self.logger.error(f"Error in parse_aljazeera: {str(e)}")

    def parse_aljazeera_article(self, response):
        try:
            item = NewsItem()
            date_results = response.css(
                'span.screen-reader-text::text, time::attr(datetime), .article-dates__published::text, .date-simple::text'
            ).getall()
            item['date'] = self.clean_text(date_results)
            event_results = response.css(
                'h1.article__title::text, h3.article-card__title span::text, header.article-header h1::text, h4.liveblog-timeline__update-content::text, h3.article-trending__title span::text, h3.gc__title span::text'
            ).getall()
            item['event'] = self.clean_text(event_results)
            item['type'] = "News Article"
            desc_results = response.css(
                'div.wysiwyg.wysiwyg--all-content p::text, div.wysiwyg p::text, p.article__subhead em::text, div.wysiwyg.wysiwyg--all-content p a::text, main#main-content-area p::text'
            ).getall()
            item['description'] = self.clean_text(desc_results)
            item['source_url'] = response.url
            item['source_name'] = "Al Jazeera"
            if item['event'] and item['description']:
                yield item
            else:
                self.logger.warning(f"Skipping blank Al Jazeera article: {response.url}")
        except Exception as e:
            self.logger.error(f"Error in parse_aljazeera_article: {str(e)}")

    # -------- CNN --------
    def parse_cnn(self, response):
        try:
            # 1. Crawl category links
            category_links = response.css(
                'a.header__nav-item-link::attr(href), a.header__nav-item-dropdown-item::attr(href), nav[data-section="sections"] a::attr(href), nav[data-analytics="header"] a::attr(href), nav a::attr(href)'
            ).getall()
            for link in category_links:
                if not link:
                    continue
                if link.startswith('/'):
                    link = f"https://edition.cnn.com{link}"
                if link not in self.visited_urls and (
                    '/world' in link or '/politics' in link or '/business' in link or '/health' in link or '/entertainment' in link or '/sport' in link or '/travel' in link
                ):
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_cnn, dont_filter=True)

            # 2. Crawl article links
            article_links = response.css(
                'a.container__link.container__link—type-article.container_lead…mages__left.container_lead-plus-headlines-with-images__light::attr(href), a.container__link.container__link—type-article.container_lead-plus-headlines__link::attr(href),  a.container__link::attr(href)'
            ).getall()
            for link in article_links:
                if not link:
                    continue
                if link.startswith('/'):
                    link = f"https://edition.cnn.com{link}"
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_cnn_article, errback=self.errback_httpbin, dont_filter=True)
        except Exception as e:
            self.logger.error(f"Error in parse_cnn: {str(e)}")

    def parse_cnn_article(self, response):
        try:
            item = NewsItem()
            item['date'] = self.clean_text(response.css(
                'div.timestamp.vossi-timestamp::text, div.timestamp::text'
            ).getall())
            item['event'] = self.clean_text(response.css(
                'h1#maincontent.headline__text.inline-placeholder.vossi-headline-text::text, h1.headline__text::text, h1.headline__text.inline-placeholder.vossi-headline-text, span.container__headline-text::text'
            ).getall())
            item['type'] = "News Article"
            item['description'] = self.clean_text(response.css(
                'p.paragraph.inline_placeholder.vossi-paragraph::text, p.paragraph-elevate.inline-placeholder.vossi-paragraph::text, div.article__content p::text'
            ).getall())
            item['source_url'] = response.url
            item['source_name'] = "CNN"
            if item['event'] and item['description']:
                yield item
            else:
                self.logger.warning(f"Skipping blank CNN article: {response.url}")
        except Exception as e:
            self.logger.error(f"Error in parse_cnn_article: {str(e)}")

    # -------- BBC --------
    def parse_bbc(self, response):
        try:
            # 1. Crawl category links
            category_links = response.css(
                'a.sc-5eaafc6a-4.eeXkpK::attr(href), nav.orb-nav a.orb-nav-link::attr(href), nav[role="navigation"] a::attr(href), nav a::attr(href)'
            ).getall()
            for link in category_links:
                if not link:
                    continue
                if link.startswith('/'):
                    link = f"https://www.bbc.com{link}"
                if link not in self.visited_urls and (
                    '/news' in link or '/sport' in link or '/reel' in link or '/worklife' in link or '/travel' in link or '/future' in link
                ):
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_bbc, dont_filter=True)

            # 2. Crawl article links
            article_links = response.css(
                'a.sc-8a623a54-0.hMvGwj::attr(href), a.media__link::attr(href)'
            ).getall()
            for link in article_links:
                if not link:
                    continue
                if link.startswith('/'):
                    link = f"https://www.bbc.com{link}"
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    yield scrapy.Request(link, callback=self.parse_bbc_article, errback=self.errback_httpbin, dont_filter=True)
        except Exception as e:
            self.logger.error(f"Error in parse_bbc: {str(e)}")

    def parse_bbc_article(self, response):
        try:
            item = NewsItem()
            item['date'] = self.clean_text(response.css(
                'time.sc-801dd632-2.IvNnh::text, time::attr(datetime)'
            ).getall())
            item['event'] = self.clean_text(response.css(
                'h2.sc-9d830f2a-3.fWzToZ::text, h1#main-heading.ssrcss-iocl1-Heading.e10rt3ze0::text, h1.sc-f98b1ad2-0.dfvxux::text, h1#main-heading::text'
            ).getall())
            item['type'] = "News Article"
            item['description'] = self.clean_text(response.css(
                'article p::text, p.sc-9a00e533-0.hxuGS::text'
            ).getall())
            item['source_url'] = response.url
            item['source_name'] = "BBC"
            if item['event'] and item['description']:
                yield item
            else:
                self.logger.warning(f"Skipping blank BBC article: {response.url}")
        except Exception as e:
            self.logger.error(f"Error in parse_bbc_article: {str(e)}")

    def errback_httpbin(self, failure):
        if failure.check(IgnoreRequest):
            self.logger.warning(f"IgnoreRequest: {failure.request.url}")
        else:
            self.logger.error(f"Error on {failure.request.url}: {repr(failure)}")
            
            
####TO RUN THE FILE
#- scrapy crawl news_scraper

###Change log level
#scrapy crawl news_scraper -s LOG_LEVEL=INFO
#scrapy crawl news_scraper -s LOG_LEVEL=DEBUG
#scrapy crawl news_scraper -s LOG_LEVEL=ERROR

###Speed & Retry Controls - Limit concurrency (requests at once)
#scrapy crawl news_scraper -s CONCURRENT_REQUESTS=4

###Set a download timeout
#scrapy crawl news_scraper -s DOWNLOAD_TIMEOUT=10

###Change retry attempts
#scrapy crawl news_scraper -s RETRY_TIMES=1

###Ignore robots.txt 
#scrapy crawl news_scraper -s ROBOTSTXT_OBEY=False


#RUN IT
#   scrapy crawl news_scraper \
#  -s CONCURRENT_REQUESTS=16 \
# -s CONCURRENT_REQUESTS_PER_DOMAIN=4 \
# -s DOWNLOAD_DELAY=0.5 \
# -s AUTOTHROTTLE_ENABLED=True \
# -s AUTOTHROTTLE_START_DELAY=1 \
# -s AUTOTHROTTLE_MAX_DELAY=5 \
# -s DOWNLOAD_TIMEOUT=20 \
# -s RETRY_ENABLED=True \
# -s RETRY_TIMES=3 \
# -s LOG_LEVEL=INFO