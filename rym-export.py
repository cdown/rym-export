#!/usr/bin/env python

import collections
import os
import re
import sys
import time
import json

import lxml.html
import requests


def sanitise_text(text):
    return re.sub(r'\s+', ' ', text.strip())


def image_to_rating(elem):
    suffix = 'm.png'
    src = elem.get('src')
    image = os.path.basename(src)
    assert image.endswith(suffix)
    rating = int(image[:-len(suffix)])
    return rating


def get_first_if_one(elems):
    if len(elems) != 1:
        raise ValueError('{!r} has {} elements, expected 1'.format(
            elems, len(elems)))

    return elems[0]


def parse_page(page, out, base_href):
    tree = lxml.html.fromstring(page)
    tree.make_links_absolute(base_href)
    rating_table = get_first_if_one(tree.xpath('//table[@class="mbgen"]'))

    for row in rating_table.xpath('.//tr[td]'):
        artists = row.xpath('.//a[@class="artist"]//text()')
        album = sanitise_text(
            get_first_if_one(row.xpath('.//a[@class="album"]//text()')))
        rating = image_to_rating(
            get_first_if_one(row.xpath(r'.//img[@height="16"]')))
        artist = ', '.join(sanitise_text(a) for a in artists)
        out[artist][album] = rating

    try:
        return tree.xpath('//a[@class="navlinknext"]')[0].get('href')
    except IndexError:
        pass


def main():
    try:
        username = sys.argv[1]
    except IndexError:
        print('Usage: {} username'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    base_href = 'https://rateyourmusic.com'
    next_uri = '{}/collection/{}/r0.5-5.0'.format(base_href, username)
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) '
            'Gecko/20100101 Firefox/54.0',
        'Referer': 'https://rateyourmusic.com/~{}'.format(username),
    }
    output = collections.defaultdict(dict)

    i = 1
    while next_uri:
        req = requests.get(next_uri, headers=headers)
        req.raise_for_status()
        next_uri = parse_page(req.text, output, base_href)
        print('Parsed page {}'.format(i), file=sys.stderr)
        i += 1
        if next_uri:
            # backoff to be nice to rym
            time.sleep(10)

    print(json.dumps(output))


if __name__ == '__main__':
    main()
