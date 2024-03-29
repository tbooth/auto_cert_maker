#!/usr/bin/env python
"""Search and replace words in a ODF document.
"""
from pathlib import Path

from odfdo import Document

IN = "form_test1.odt"
OUT = "form_test1_replaced.odt"


def save_new(document: Document, name: str):
    print("Saving:", name)
    # FIXME - what do pretty do?
    document.save(name, pretty=True)


def search_replace(document):
    body = document.body

    # replace a string in the full document
    body.replace("REPLACEME", "New Text Here")

    # replace in paragraphs only
    for paragraph in body.get_paragraphs():
        paragraph.replace("REPLACEME", "Woo woo woo")


def main():
    document = Document(IN)
    search_replace(document)
    save_new(document, OUT)


if __name__ == "__main__":
    main()
