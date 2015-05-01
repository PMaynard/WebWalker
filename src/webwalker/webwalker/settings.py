# -*- coding: utf-8 -*-

# Scrapy settings for webwalker project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'webwalker'

SPIDER_MODULES = ['webwalker.spiders']
NEWSPIDER_MODULE = 'webwalker.spiders'

LOG_LEVEL="INFO"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'webwalker (+http://nationpigeon.com)'
