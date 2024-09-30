#!/usr/bin/env python3

import argparse
import zipfile
from dataclasses import dataclass
from pathlib import Path

import xmltodict
from yarl import URL


ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}


class EltMixin:

    @classmethod
    def list_from_dict(cls, data):
        if data is None:
            return []
        if type(data) is list:
            obj_list = [cls.from_dict(elt) for elt in data]
        else:
            obj_list = [cls.from_dict(data)]
        return [obj for obj in obj_list if obj is not None]


@dataclass
class Author(EltMixin):
    first_name: str
    last_name: str
    nick: str
    home_page: URL

    @classmethod
    def from_dict(cls, data):
        self = cls(
            first_name=data.get('first-name'),
            last_name=data.get('last-name'),
            nick=data.get('nickname'),
            home_page=data.get('home-page'),
            )
        if not self.first_name and not self.last_name and not self.nick:
            # Nothing is defined, should try another section.
            return None
        return self

    def __str__(self):
        elts = [self.last_name, self.first_name]
        result = ' '.join(filter(None, elts))
        if result:
            if self.nick:
                return f'{result} ({self.nick})'
            else:
                return result
        else:
            return self.nick or ''


@dataclass
class Sequence(EltMixin):
    name: str
    num: int

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['@name'],
            num=data.get('@number', '0'),
            )

    def __str__(self):
        return f'{self.name}-{self.num}'


def genre_from_dict(data):
    if data is None:
        return None
    if type(data) is dict:
        return data['#text']
    else:
        assert type(data) is str, repr(data)
        return data


def genre_list_from_dict(data):
    if data is None:
        return []
    if type(data) is list:
        genre_list = [genre_from_dict(elt) for elt in data]
    else:
        genre_list = [genre_from_dict(data)]
    return [g for g in genre_list if g]


def parse_fb2(text):
    body_tag = b'<body>'
    body_idx = text.find(body_tag)
    if body_idx != -1:
        # Some books have invalid markup inside it's body. Try to just drop it.
        # This also speeds things up a little.
        text = text[:body_idx] + b'<body/></FictionBook>'
    root = xmltodict.parse(text)
    title_info = root['FictionBook']['description']['title-info']
    doc_info = root['FictionBook']['description'].get('document-info')
    author_list = Author.list_from_dict(title_info.get('author'))
    if not author_list and doc_info:
        author_list = Author.list_from_dict(doc_info.get('author'))
    seq_list = Sequence.list_from_dict(title_info.get('sequence'))
    title = title_info['book-title']
    genre_list = genre_list_from_dict(title_info.get('genre'))
    author_elt = ', '.join(str(author) for author in author_list)
    if not author_elt:
        author_elt = 'Unknown author'
    elements = [author_elt]
    if seq_list:
        elements.append(', '.join(str(seq) for seq in seq_list))
    elements.append(str(title))
    return ' / '.join(elements) + ', genres: ' + ', '.join(genre_list)


def process_file(path):
    print(f"Processing file: {path}")
    zip_file = zipfile.ZipFile(path)
    i = 0
    for name in zip_file.namelist():
        if not name.endswith('.fb2'):
            continue
        with zip_file.open(name) as f:
            bytes = f.read()
            try:
                info_text = parse_fb2(bytes)
            except:
                tmp_path = Path('/tmp') / name
                tmp_path.write_bytes(bytes)
                print(f"While parsing {path}/{name}, written to {tmp_path}:")
                raise
            print(f"  {name}: {info_text}")
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
