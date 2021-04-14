# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JdItem(scrapy.Item):
    # define the fields for your item here like:
    # 大分类
    big_category = scrapy.Field()
    # 大分类链接
    big_category_link = scrapy.Field()
    # 小分类
    small_category = scrapy.Field()
    # 小分类链接
    small_category_link = scrapy.Field()
    # 书名
    book_name = scrapy.Field()
    # 作者
    author = scrapy.Field()
    # 书的链接
    link = scrapy.Field()
    # 价格
    price = scrapy.Field()


    pass


















