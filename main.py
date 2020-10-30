import argparse
from asyncio import get_event_loop
from os import getcwd
from tempfile import NamedTemporaryFile
from time import time

from aiohttp import ClientOSError
from aiohttp import ClientPayloadError
from aiohttp import ClientSession
from aiohttp import InvalidURL
from lxml.etree import ElementTree
from lxml.etree import ParserError
from lxml.etree import XMLSyntaxError
from lxml.html import fromstring
from lxml.html import HTMLParser


HTTP_EXCEPTIONS = (
    ClientOSError,
    ClientPayloadError,
    InvalidURL,
    OSError,
    TimeoutError,
)

HTML_ENCODING = 'utf-8'
CONTENT_PATH = '//*[@id="colleft"]/descendant-or-self::div[@class="box"]'
BAD_XPATHS = (
    '//div[contains(@id, "buttons")]',
    '//div[@align="right"]',
    '//div[@id="tl"]',
    '//p[@class="buttons"]',
    '//script',
)


async def _main(url):
    options = dict(headers={'User-Agent': 'Mozilla/5.0'})
    async with ClientSession(**options) as session:
        try:
            resp = await session.get(url, allow_redirects=False)
        except HTTP_EXCEPTIONS:
            raise SystemExit('Error while downloading content')

        async with resp:
            if resp.status != 200:
                raise SystemExit(f'Ivalid HTTP response: {resp.status}')

            try:
                html = await resp.text()
            except TimeoutError:
                raise SystemExit('Timeout while reading content')

    try:
        root = fromstring(html, parser=HTMLParser(collect_ids=False))
    except (ParserError, XMLSyntaxError):
        raise SystemExit('Error while parsing content')

    try:
        content, = root.xpath(CONTENT_PATH)
    except ValueError:
        raise SystemExit('Multiple results while parsing the content')

    for xpath in BAD_XPATHS:
        for bad in content.xpath(xpath):
            bad.getparent().remove(bad)

    with NamedTemporaryFile(
            mode='w+b',
            suffix='.html',
            prefix=f'{int(time())}_',
            dir=getcwd(),
            delete=False,
    ) as html_file:
        ElementTree(content).write(html_file, encoding=HTML_ENCODING)


def main():
    parser = argparse.ArgumentParser(prog='lex-dl')
    parser.add_argument(
        '-V', '--version', action='version', version='%(prog)s 0.0.1',
    )
    parser.add_argument('url', type=str, help='Lex BG page url')
    args = parser.parse_args()

    loop = get_event_loop()
    try:
        exit(loop.run_until_complete(_main(args.url)))
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == '__main__':
    main()
