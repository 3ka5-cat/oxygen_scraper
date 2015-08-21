# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from scrapy.item import Item, Field

"""
Result item should looks like:
{
    'code': 'Ribbon-Landscape-Sweatshirt',
    'color': 'green',
    'description': u"Ribbon landscape sweatshirt by clover canyon.
                    White curved stripes add a fun ribbon effect over the floral print on this
                    fleece lined jumper. It has a deep 'v' neckline and contrasting ribbing on
                    the cuffs and hem. Deep 'v' neckline same day (london only within the m25)
                    - \xa315 - same day delivery using dhl. If saturday delivery is required
                    please call the store.",
    'designer': 'Clover Canyon',
    'gender': 'F',
    'image_urls': ['http://www.oxygenboutique.com/GetImage/cT0xMDAmdz04MDAmaD02MDAmUEltZz1hOTBjOWRmNS0zNGEzLTQ3OTYtOTAwMy05ZTdkNWY0Y2RmMDguanBn0.jpg',
                'http://www.oxygenboutique.com/GetImage/cT0xMDAmdz04MDAmaD02MDAmUEltZz00OWQxMjViYy02MGVlLTQ2NmYtODBiNC04MmQ3YmUwNzE5MzMuanBn0.jpg',
                'http://www.oxygenboutique.com/GetImage/cT0xMDAmdz04MDAmaD02MDAmUEltZz1hYzM3NzY0ZC0yMTg4LTRmZDctOTRhMC0yODIyYmIyNzAxYTMuanBn0.jpg',
                'http://www.oxygenboutique.com/GetImage/cT0xMDAmdz04MDAmaD02MDAmUEltZz01Nzk5ZmZhZS04NzQ4LTQ5ZTgtOTIyOS02OTlkMzM1ZTNmNTUuanBn0.jpg'],
    'link': 'http://www.oxygenboutique.com/Ribbon-Landscape-Sweatshirt.aspx',
    'name': u'Ribbon Landscape Sweatshirt',
    'raw_color': u'clover',
    'sale_discount': 70.0,
    'stock_status': {'L': 3, 'M': 3, 'S': 3, 'XS': 1},
    'type': 'A',
    'usd_price': '430.91'
}

Note that some fields are clearcut (gbp_price must equal 255.00 GBP),
whereas some fields are open to interpretation (e.g. description),
where arguably we could have included either more or less than in the sample here,
and code, which should just be an identifier unique to this retailer.

Field details

    type, try and make a best guess, one of:
        'A' apparel
        'S' shoes
        'B' bags
        'J' jewelry
        'R' accessories
    gender, one of:
        'F' female
        'M' male
    designer - manufacturer of the item
    code - unique identifier from a retailer perspective
    name - short summary of the item
    description - fuller description and details of the item
    raw_color - best guess of what colour the item is (can be blank if unidentifiable)
    image_urls - list of urls of large images representing the item
    usd_price - full (non-discounted) price of the item
    sale_discount - percentage discount for sale items where applicable
    stock_status - dictionary of sizes to stock status
        1 - out of stock
        3 - in stock
    link - url of product page

"""


class OxygenItem(Item):
    code = Field()
    color = Field()
    description = Field()
    designer = Field()
    gender = Field()
    image_urls = Field()
    link = Field()
    name = Field()
    raw_color = Field()
    sale_discount = Field()
    stock_status = Field()
    type = Field()
    usd_price = Field()

