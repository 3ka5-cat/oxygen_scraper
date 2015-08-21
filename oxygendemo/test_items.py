# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from pprint import pprint

if __name__ == "__main__":
    """ Reads json file with results of scraping and
    write items with different types into separate json files.
    Used for visual testing of scraper's logic while developing.
    """
    shoes = []
    clothes = []
    accs = []
    with open('items.json') as data_file:
        data = json.load(data_file)
        for item in data:
            if item['type'] is None:
                pprint(item)
            if item['type'] == 'S':
                shoes.append(item['name'])
            if item['type'] == 'R':
                accs.append(item['name'])
            if item['type'] == 'A':
                clothes.append(item['name'])

    with open('accs.json', 'w') as outfile:
        json.dump(accs, outfile)

    with open('shoes.json', 'w') as outfile:
        json.dump(shoes, outfile)

    with open('clothes.json', 'w') as outfile:
        json.dump(clothes, outfile)