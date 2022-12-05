#!/usr/bin/env python
import timeit

from typing import Dict, List
from word_forms.word_forms import get_word_forms


def _generate_data(db):
    for i, row in enumerate(open('./transcript.txt', 'r').readlines()):
        if row.strip():
            index(db, {f'line {i}': row.strip()}, id_=i)


class Database:
    def __init__(self):
        self.__docs: dict[int, Dict[str, str]] = {}
        self.__index: dict[str, set[int]] = {}
        self.__doc_ids: set[int] = set()

    def index(self, doc: Dict[str, str], id_: int = None) -> None:
        self.__reindex_if_doc_in_db(id_)
        self.__doc_ids.add(id_)
        self.__docs[id_] = doc
        words = set()

        for word in self.__lower_strip_words(doc):
            words.add(word)

            for variations in get_word_forms(word).values():
                for variation in variations:
                    words.add(variation)

        for variation in words:
            self.__init_index_entry(variation)
            self.__index[variation].add(id_)

    def __reindex_if_doc_in_db(self, id_: int) -> None:
        empty_buckets: List[str] = list()

        if id_ in self.__doc_ids:
            doc: Dict[str, str] = self.__docs[id_]

            for word in self.__lower_strip_words(doc):
                if word in self.__index and id_ in self.__index[word]:
                    self.__index[word].remove(id_)
                    if len(self.__index[word]) == 0:
                        empty_buckets.append(word)

            for word in empty_buckets:
                del self.__index[word]

    def __init_index_entry(self, word: str) -> None:
        if word not in self.__index:
            self.__index[word] = set()

    def __lower_strip_words(self, doc: Dict[str, str]) -> set[str]:
        words: set[str] = set()

        for value in doc.values():
            for word in value.split():
                words.add(self.__strip_key(word.lower()))

        return words

    @staticmethod
    def __strip_key(key: str) -> str:
        if key[-1] in [',', '!', '.']:
            key = key[:-1]
        return key

    def match(self, text: str) -> List[int]:
        match_ids: set[int] = set()

        for i in text.split():
            key = i.lower()

            if key in self.__index:
                match_ids.update(self.__index[key])

        return list(match_ids)


def index(db, doc: Dict[str, str], id_: int = None):
    """
    Stores the document and have it available to search.

    :param db: The data structure to use.
    :param doc: A one level hierarchy dict.
    :param id: The ID for the given doc, or None for automatic ID.
    """
    db.index(doc, id_)


def match(db, text: str) -> List[int]:
    """
    Returns the IDs of documents that contained ANY of the words in this text.
    This operation is case-insensitive.

    :param db: The data structure to use.
    :param text: text that we want to search for.
    :return: The list of matching document IDs.
    """
    return db.match(text)


if __name__ == '__main__':
    # Change this line to point to your DB object.
    db = Database()

    ### Sanity Tests ###

    # Step 1:

    index(db, {'Sheldon': 'Our whole universe was in a hot, dense state'}, id_=1)

    assert match(db, 'universe') == [1], 'The word "universe" should appear in the DB'

    # Step 2:

    index(db, {'Lenoard': 'Then nearly fourteen billion expansion ago expansion started, wait!'}, id_=1)

    assert match(db, 'It all started with the big bang!') == [1], 'The word "started" should appear in the DB'
    assert match(db, 'AGO') == [1], 'The word "ago" should appear in the DB'

    # Step 3:

    index(db, {'Penny': "Our best and brightest figure that it'll make an even bigger bang!"}, id_=1)
    index(db, {'Penny': 'Music and mythology, Einstein and astrology', 'Raj': 'It all started with the big bang!'},
          id_=2)

    assert match(db, 'BANG') == [1, 2], 'The word "bang" should appear in the DB multiple times'

    # Step 4:

    index(db, {'Howard': "It's expanding ever outward but one day"}, id_=1)
    assert match(db, 'expanding') == [1], 'Document with id = 1 contains the word "expanding"'

    index(db, {'Bernadette': "Our best and brightest figure that it'll make an even bigger bang!"}, id_=1)
    assert match(db,
                 'expanding') == [], 'Document with id = 1 was overriden by a new doc that does not contain the word expanding'
    assert match(db, 'brightest') == [1], 'Document with id = 1 contains the word "brightest"'

    # Step 5:

    index(db, {'Sheldon': 'It doesn\'t need proving'}, id_=1)

    assert match(db, 'prove') == [
        1], 'Our search should support variations match, so in this case it should find all documents containing - proving, prove, proves, proved..'

    # Step 6:

    _generate_data(db)
    assert len(match(db, 'jedi')) >= 70, 'expected more appearances of the word "jedi"'

### Performance Tests ###


import time


class Timer:
    def __init__(self):
        self.start = None
        self.end = None
        self.duration = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        self.duration = self.end - self.start


_generate_data(db)
t = Timer()
with t:
    match(db, 'jedi')

assert t.duration < 0.0001, 'Too slow :('
