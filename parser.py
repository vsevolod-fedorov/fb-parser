#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}


def parse_fb2(text):
    root = ET.fromstring(text)
    title_info = root.find('.//fb:title-info', ns)
    print(title_info.find('fb:book-title', ns).text)
    seq = title_info.find('fb:sequence', ns)
    if seq is not None:
        print(seq.get('name'), "#", seq.get('number'))
    for author in title_info.findall('fb:author', ns):
        print(author.find('fb:first-name', ns).text, author.find('fb:last-name', ns).text)
        nickname = author.find('fb:nickname')
        if nickname is not None:
            print(nickname.text)
    for genre in title_info.findall('fb:genre', ns):
        print("Genre:", genre.text)


def process_file(path):
    print(f"Processing file: {path}")
    zip_file = zipfile.ZipFile(path)
    i = 0
    for name in zip_file.namelist():
        if not name.endswith('.fb2'):
            continue
        print(f"  Book: {name}")
        with zip_file.open(name) as f:
            text = f.read()
            info = parse_fb2(text)
            # print(f"    {info}")
        i += 1
        if i > 100:
            break


def process_path(path):
    if path.is_dir():
        for file_path in path.rglob('*.zip'):
            process_file(file_path)
    else:
        process_file(path)


def main():
    parser = argparse.ArgumentParser(description='Compile resources')
    parser.add_argument('path', type=Path, nargs='*', help="Dir or zip file paths to process")
    args = parser.parse_args()

    for path in args.path:
        process_path(path)

        
if __name__ == '__main__':
    main()
