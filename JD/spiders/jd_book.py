# -*- coding: utf-8 -*-
import scrapy
import time
from scrapy import Selector
from urllib import parse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from mouse import move, click
from JD.items import JdItem
import json

# 分布式爬虫的步骤
# -----1导入分布式爬虫类
from scrapy_redis.spiders import RedisSpider


# -----2 继承分布式爬虫类
class JdBookSpider(RedisSpider):
    name = 'jd_book'

    # -----3注销：start_urls和allowed_domains
    # # 允许修改的域
    # allowed_domains = ['www.jd.com', 'list.jd.com', 'p.3.cn']
    # # 这是起始url
    # start_urls = ['https://book.jd.com/booksort.html']

    # ----4 设置redis-key,这个key 随意设置，但是所有爬虫都要从这个key找起始url，也是往里放数据，也从里面取
    # 在redis中输入lpush py21 https://book.jd.com/booksort.html
    redis_key = 'py21'

    # ----5 设置__init__
    def __init__(self, *args, **kwargs):
        # 在初始化的时候是获取domain参数，如果没有则为空字符串。
        domain = kwargs.pop('domain', '')

        # 我们在domain是可能有多个允许的域，所以用domain.split(',')， 用逗号隔开
        # ['www.jd.com', 'list.jd.com', 'p.3.cn']就是这样的域
        # filter要转换成一个列表
        self.allowed_domains = list(filter(None, domain.split(',')))
        super(JdBookSpider, self).__init__(*args, **kwargs)

    def parse(self, response):

        # 1.要想无界面启动selenium，先设置headless模式
        chrome_options = Options()  # 实例化这个Options(),要在webdriver.Chrome加上参数
        chrome_options.add_argument("--headless")   # 这个就是无界面启动selenium，一定要写的
        chrome_options.add_argument("--disable-gpu")  # 谷歌文档提到需要加上这个属性来规避bug

        # 2.设置selenium不加载图片, blink-settings=imagesEnabled=false是固定的
        # chrome_options.add_argument("blink-settings=imagesEnabled=false")

        """
        1.启动chrome（启动之前确保所有的chrome实例己经关闭）
        """
        browser = webdriver.Chrome(executable_path="D:/DecomPression-File/chromedriver_win32 (2.45-70)/chromedriver.exe", chrome_options=chrome_options)

        browser.get("https://book.jd.com/booksort.html")

        # page_source就是运行js完后的html网页
        sel_css = Selector(text=browser.page_source)

        time.sleep(3)
        # 获取所有图书大分类节点列表
        big_node_list = sel_css.xpath('//*[@id="booksort"]/div[2]/dl/dt/a')
        # print(len(big_node_list))

        # 循环拿出所有图书名和url
        # for big_node in big_node_list:
        #     big_category = big_node.xpath('./text()').extract_first()
        #     # 这里会自己加入https://,这就是urljoin的好处
        #     # 不用写ht= 'https://'，直接用urljoin也能直接拼接https://,因为自带
        #     ht = 'https://'
        #     big_category_link_url = big_node.xpath('./@href').extract_first()
        #     big_category_link = parse.urljoin(ht, big_category_link_url)
        #
        #     print(big_category, big_category_link)

        """循环拿出所有图书名和url"""
        for big_node in big_node_list[:2]:
            """这两个是获取大分类的名字和url"""
            big_category = big_node.xpath('./text()').extract_first()
            # 这里会自己加入https://,这就是urljoin的好处
            # 不用写ht= 'https://'，直接用urljoin也能直接拼接https://,因为自带
            big_category_link = response.urljoin(big_node.xpath('./@href').extract_first())
            # print(big_category, big_category_link)

            # 在大节点上(//*[@id="booksort"]/div[2]/dl/dt/a)获取所有图书小分类节点列表
            small_node_list = big_node.xpath('../following-sibling::dd[1]/em/a')
            # print(len(small_node_list))

            for small_node in small_node_list[:5]:
                temp = {}

                # 取下大分类名
                temp['big_category'] = big_category
                # # 取下大分类名url
                temp['big_category_link'] = big_category_link
                # 取下小分类名
                temp['small_category'] = small_node.xpath('./text()').extract_first()
                temp['small_category_link'] = response.urljoin(small_node.xpath('./@href').extract_first())
                # print(temp)

                # 模拟点击小分类链接
                # meta=temp是小分类的链接是来处哪里的
                # temp['small_category_link']是小分类的url，然后放在meta下的字典，传给下一个函数
                yield scrapy.Request(
                    url=temp['small_category_link'], callback=self.parse_book_list, meta={"py21": temp}
                )

    def parse_book_list(self, response):
        # 爬取图片列表页面
        temp = response.meta['py21']

        # 1.要想无界面启动selenium，先设置headless模式
        chrome_options = Options()  # 实例化这个Options(),要在webdriver.Chrome加上参数
        chrome_options.add_argument("--headless")  # 这个就是无界面启动selenium，一定要写的
        chrome_options.add_argument("--disable-gpu")  # 谷歌文档提到需要加上这个属性来规避bug

        # 2.设置selenium不加载图片, blink-settings=imagesEnabled=false是固定的
        # chrome_options.add_argument("blink-settings=imagesEnabled=false")

        """
        1.启动chrome（启动之前确保所有的chrome实例己经关闭）
        """
        browser = webdriver.Chrome(
            executable_path="D:/DecomPression-File/chromedriver_win32 (2.45-70)/chromedriver.exe",
            chrome_options=chrome_options)

        # 把小分类里的url放在selenium中
        browser.get(temp['small_category_link'])

        # page_source就是运行js完后的html网页
        temp_xc = Selector(text=browser.page_source)

        time.sleep(3)

        # 把这一页面己经渲染的书拿在这里，下面在基础上再进一步提取
        book_list = temp_xc.xpath('//*[@id="J_goodsList"]/ul/li/div')
        # print(len(book_list))

        # 抽取图书信息
        for book in book_list:
            item = JdItem()
            # 我们会存取在temp的数据，temp里面的都是大的节点，
            # 而在book_list中的的图书信息都是temp的子集
            """存放在大节点的temp中的图书数据"""
            item['big_category'] = temp['big_category']
            item['big_category_link'] = temp['big_category_link']
            item['small_category'] = temp['small_category']
            item['small_category_link'] = temp['small_category_link']

            item['book_name'] = book.xpath('./div[3]/a/em/text()').extract_first()
            item['author'] = book.xpath('./div[4]/span[1]/a/text()').extract_first()
            item['link'] = response.urljoin(book.xpath('./div[1]/a/@href').extract_first())

            # 这样取价格也可以
            # item['price'] = book.xpath('./div[2]/strong/i/text()').extract_first()
            # print(item)

            # .//相对节点，，，，./是当前节点,相对节点更好一点
            # 获取图书编号
            skuid = book.xpath('.//@data-sku').extract_first()
            # skuid = book.xpath('./@data-sku').extract_first()
            # print("skuid:", skuid)

            # 这样取出这个id，然后加url，最后返回一个的js，里面就有价格
            # 拼接图书价格地址
            pri_url = 'https://p.3.cn/prices/mgets?skuIds=J_' + skuid

            # meta是要从上面这个函数传到下面这个函数
            yield scrapy.Request(url=pri_url, callback=self.parse_price, meta={'meta_1': item})

    def parse_price(self, response):
        item = response.meta['meta_1']
        # print(response.body)

        dict_data = json.loads(response.body)
        item['price'] = dict_data[0]['p']
        yield item



















