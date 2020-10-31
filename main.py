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
CONTENT_PATH = '//*[@id="colleft"]/descendant::div[@class="boxi boxinb"]'
BAD_XPATHS = (
    '//div[contains(@id, "buttons")]',
    '//div[@align="center" or @align="right"]',
    '//div[@id="tl"]',
    '//p[@class="buttons"]',
    '//script',
)


def export(html, custom_filename=''):
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

    if custom_filename:
        filename = custom_filename
    else:
        file_options = dict(
            mode='w+b',
            suffix='.html',
            prefix=f'{int(time())}_',
            dir=getcwd(),
            delete=False,
        )
        with NamedTemporaryFile(**file_options) as html_file:
            filename = html_file.name

    ElementTree(content).write(filename, encoding=HTML_ENCODING)


async def _main(args):
    options = dict(headers={'User-Agent': 'Mozilla/5.0'})
    async with ClientSession(**options) as session:
        try:
            resp = await session.get(args.url, allow_redirects=False)
        except HTTP_EXCEPTIONS:
            raise SystemExit('Error while downloading content')

        async with resp:
            if resp.status != 200:
                raise SystemExit(f'Ivalid HTTP response: {resp.status}')

            try:
                html = await resp.text()
            except TimeoutError:
                raise SystemExit('Timeout while reading content')

    await get_event_loop().run_in_executor(None, export, html, args.output)


def main():
    parser = argparse.ArgumentParser(prog='lex-dl')
    parser.add_argument(
        '-V', '--version', action='version', version='%(prog)s 0.0.1',
    )
    parser.add_argument('-o', '--output', help='Write output to specific file')
    parser.add_argument('url', help='Lex BG page url')
    args = parser.parse_args()

    loop = get_event_loop()
    try:
        exit(loop.run_until_complete(_main(args)))
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == '__main__':
    main()
