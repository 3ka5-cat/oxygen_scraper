# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import re
import urlparse
from decimal import Decimal
from pyquery import PyQuery as pq
from scrapy import log
from scrapy.http import FormRequest, Request
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from ..items import OxygenItem


# We could extract list of items from page of each category, but it's boring
# Let's get all items from search page with empty search query and guess item's type by heuristic
class OxygenSpider(CrawlSpider):
    name = "oxygen"
    allowed_domains = ["www.oxygenboutique.com"]
    start_urls = [
        "http://www.oxygenboutique.com/SearchResults.aspx?ViewAll=1",
    ]
    rules = (
        Rule(SgmlLinkExtractor(allow=('.aspx$', ), restrict_xpaths=('//div[@class="itm"]', )),
             callback='parse_item'),
    )

    # regexps for price
    price_regexp = re.compile(ur'([£$]\s*)(\d+\.\d{2}\s*)(\d+\.\d{2})?')
    sold_out_regexp = re.compile(r'\s*-\s*sold\s*out', re.IGNORECASE)
    # regexp for sizes
    onesize_regexp = re.compile(r'one\s*size', re.IGNORECASE)
    alpha_size_regexp = re.compile(r'\b(XXS|XS|S|M|L|XL|XXL|XXXL)\b', re.IGNORECASE)
    others_size_regexp = re.compile(r'(\d+\.?\d{,1})')
    # attributes for size determination heuristics
    shoe_category_url = 'http://www.oxygenboutique.com/Shoes-All.aspx?ViewAll=1'

    def start_requests(self):        
        # search returns 500 if it wasn't properly called from this damn asp.net form 
        # and there are no session cookie, possibly it is because of weird caching,
        # because, moreover, search view remembers last search, and returns it instead of all items
        # when empty search query passed to search view.
        # So we must make initial request first for the registration of new session, 
        # also we should set currency to USD instead of by-default GBP,
        # let's make it in one request
        return [Request("http://www.oxygenboutique.com/currency.aspx", callback=self.set_currency)]

    # def make_requests_from_url(self, url):
    #     """Manually set session for development purposes. More details in start_requests docstring"""
    #     request = super(OxygenSpider, self).make_requests_from_url(url)
    #     request.cookies['ASP.NET_SessionId'] = 'b21uehs1vpzzcvjgl3ytfnov'
    #     return request

    def set_currency(self, response):
        """Change currency into USD before scraping start."""
        doc = pq(response.body)
        formdata = {'__EVENTTARGET': 'lnkCurrency',
                    '__VIEWSTATE': doc('#__VIEWSTATE').attr('value'),
                    'ddlCurrency': doc(':contains("USD")').attr('value')}
        return FormRequest("http://www.oxygenboutique.com/currency.aspx", 
                           formdata=formdata,
                           callback=self.start_scraping)

    def start_scraping(self, response):
        return super(OxygenSpider, self).start_requests()
    
    def parse_item(self, response):
        doc = pq(response.body)
        item = OxygenItem()
        item['link'] = response.url
        # oxygen sells only female items
        item['gender'] = 'F'
        # get slug as code
        path = urlparse.urlparse(response.url).path
        # get only last part of path
        cleaned_path = path.rsplit('/', 1)[1]
        # without extension
        item['code'] = os.path.splitext(cleaned_path)[0]
        item['raw_color'] = self.determine_color()
        item['color'] = self.map_color(item['raw_color'])
        item['description'] = doc('#accordion>:contains("Description")+div').text()
        item['designer'] = doc('.brand_name>a').text()
        item['image_urls'] = [urlparse.urljoin(response.url, image_link.attr('href').strip()) for image_link in
                              doc('#product-images').find('#thumbnails-container').find('a').items()]
        item['name'] = doc('div.breadcrumb').find('a:last').parent().clone().remove('a').text()
        item.update(self.get_price_and_discount(doc('.price').text()))
        sizes = doc('#ppSizeid').find('select option')
        item.update(self.get_stock_status(sizes))
        item.update(self.determine_type(item['name'], sizes))
        return item

    def get_price_and_discount(self, text):
        """
        Gets item's price and calculates sale discount in percents.
        :param text: text of HTML element, which contains price info
        :return: dict with price in rendered currency and sale discount
        """
        price_dict = {}
        parsed_price = self.price_regexp.search(text).groups()
        price = Decimal(parsed_price[1])
        if parsed_price[0] != '$':
            self.log("Currency wasn't changed to USD", log.WARNING)
        price_dict['usd_price'] = price
        discounted_price = Decimal(parsed_price[2]) if parsed_price[2] else 0
        price_dict['sale_discount'] = round(discounted_price / price, 2)
        return price_dict

    def get_stock_status(self, text):
        """
        Maps available sizes into stock statuses.
        :param text: list of HTML options from size select form
        :return: dict with stock statuses of listed sizes
        """
        def map_stock_status(index, element):
            # skip first element with index 0
            if index:
                # check sold out size
                is_sold_out = self.sold_out_regexp.search(element.text) is not None
                # set appropriate enum value, remove sold out mark if needed                
                return (re.sub(self.sold_out_regexp, '', element.text), 1) if is_sold_out else (element.text, 3)
            else:
                return None

        return {'stock_status': dict(text.map(map_stock_status))}

    # TODO: implement color getting
    def determine_color(self):
        pass

    def map_color(self, color):
        pass

    def check(self, item_name):
        """
        Makes request to shoe category with ?ViewAll=1, if exist code -- shoe, else apparel.
        :param item_name: name of item for checking
        :return: type's value: 'A' or 'S'
        """
        # Instead of request we could store some kind of vocab for checking item's name
        doc = pq(self.shoe_category_url)
        for element in doc('.itm h3'):
            if item_name in element.text:
                return 'S'
        return 'A'

    def determine_type_of_alpha_sizes(self, item_name, alpha_sizes):
        """
        Heuristic determination of item's type.
        :param item_name: name of item
        :param alpha_sizes: list of strings representing all existing (not only stocked) sizes
        :return: type's value: 'A' or 'S'
        """
        # unfortunately, nonlocal working only in python 3, so updating these variables,
        # we should declare them as class attributes
        self.min_size = 0
        self.max_size = 0
        self.exist_fractional_part = False
        self.even_sizes = []
        self.odd_sizes = []

        def map_numerical_sizes(size):
            try:
                numerical_size = float(size)
            except ValueError:
                self.log('Can\'t cast size into float', level=log.ERROR)
                return None

            if numerical_size % 2 == 0:
                self.even_sizes.append(numerical_size)
            else:
                self.odd_sizes.append(numerical_size)

            if not numerical_size.is_integer():
                self.exist_fractional_part = True

            # initialize min_size with first numerical_size and keep comparing for finding minimum
            self.min_size = numerical_size if not self.min_size or numerical_size < self.min_size else self.min_size
            self.max_size = numerical_size if numerical_size > self.max_size else self.max_size
            return numerical_size

        numerical_sizes = map(map_numerical_sizes, alpha_sizes)
        num_of_existing_sizes = len(alpha_sizes)
        # in accordance with size chart from oxygen
        # if there is a size with fractional part -- it is shoes
        if self.exist_fractional_part:
            return 'S'
        # check case when only one size is existing
        if num_of_existing_sizes == 1:
            return self.check(item_name)
        # all sizes are even or odd (for Japan) -- apparel,
        # also check for special case of australian swimwear,
        # also we assume that step of shoe sizing unlikely be more than 1.5
        if self.min_size in [0, 1] or \
                        num_of_existing_sizes == len(self.even_sizes) or \
                        num_of_existing_sizes == len(self.odd_sizes):
            return 'A'
        # special case of australian swimwear, when it can be confused with shoe
        elif '2' in alpha_sizes or '3' in alpha_sizes:
            return self.check(item_name)
        # although, it isn't noted at size chart,
        # sizes of clothes could compose increasing integer sequence with step=1
        # (numbers with fractional part we proceed already as shoe sizes), so this case is handled here
        # But...
        # there are some ugliness: numerical_sizes list of floats, min and max sizes are floats too,
        # but range doesn't accept floats... however above we are already proceed numbers with fractional part,
        # so we can safely cast min and max to integers
        elif numerical_sizes == map(float, xrange(int(self.min_size), int(self.max_size+1))):
            return self.check(item_name)
        # all others are shoes
        else:
            return 'S'

    def determine_type(self, item_name, text):
        """
        There are no jewelry or bags on oxygen, so possible types are 'A' apparel, 'S' shoes and 'R' accessories.
        :param item_name: name of item
        :param text:
        :return: dict with type field
        """
        # remove info about sold out sizes and join all sizes into one string for regexp searching
        sizes = ','.join(text.map(lambda i, e: re.sub(self.sold_out_regexp, '', e.text) if i else None))
        result = {'type': None}
        match = self.onesize_regexp.search(sizes)
        # if only only one size is available -- accessories
        if match is not None:
            result['type'] = 'R'
        else:
            match = self.alpha_size_regexp.search(sizes)
            # if one of x* notation sizes -- apparel
            if match is not None and match.groups():
                result['type'] = 'A'
            else:
                alpha_sizes = self.others_size_regexp.findall(sizes)
                if alpha_sizes:
                    result['type'] = self.determine_type_of_alpha_sizes(item_name, alpha_sizes)
        return result