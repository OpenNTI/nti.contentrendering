#!/usr/bin/env python
# -*- coding: utf-8 -
"""
HTML5 microdata parser for python 2.x/3.x

- it requires lxml
- microdata specification: http://dev.w3.org/html5/md/

https://gist.github.com/577116

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sys
from six.moves.urllib_parse import urljoin

import lxml.html as lhtml

PROPERTIES_KEY = 'properties'

logger = __import__('logging').getLogger(__name__)


def items(html, types=None, uri=""):
    """
    list microdata as standard data types
    returns [{"properties": {name: [val1, ...], ...}, "id": id, "type": type}, ...]
    """
    doc = lhtml.fromstring(html)
    return Microdata(doc, uri).items(types)


class Microdata(object):

    def __init__(self, doc, uri=""):
        self.base = uri
        self.doc = doc
        self.find_base()
        self.cache = {}

        # data factory
        self.url = urljoin
        self.text = lambda t: t
        self.datetime = lambda dt: dt

    def items(self, types=None):
        ret = []
        for elem in self.item_elems(self.doc, types):
            item = self.parse_item_elem(elem, {})
            ret.append(item)
        return ret

    def item_elems(self, elem, types=None):
        """
        iterate top-level items of elements
        """

        if (elem.get("itemscope") is not None and elem.get("itemprop") is None):
            if not types or elem.get("itemtype") in types:
                yield elem

        for child in elem.getchildren():
            for ele in self.item_elems(child, types):
                yield ele

    def parse_item_elem(self, elem, item):
        props = {}
        item[PROPERTIES_KEY] = props

        refs = elem.get("itemref")
        if refs is not None:
            for ref in refs.split():
                self.parse_item_ref(props, ref)

        for child in elem.getchildren():
            self.parse_item_props(child, props, None)

        attrs = elem.keys()

        if "itemid" in attrs:
            item["id"] = elem.get("itemid")

        if "itemtype" in attrs:
            item["type"] = elem.get("itemtype")

        return item

    def parse_item_ref(self, props, ref):
        if ref not in self.cache:
            self.cache[ref] = {}
            child = self.elem_by_id(self.doc, ref)
            self.parse_item_props(child, {}, ref)

        for name in self.cache[ref]:
            if name not in props:
                props[name] = []
            props[name].extend(self.cache[ref][name])

    def parse_item_props(self, elem, props, ref):
        if elem is None:
            return

        propnames = elem.get("itemprop")
        if propnames:
            names = propnames.split()
            value = self.parse_value(elem, ref, names)
            for propname in names:
                if propname not in props:
                    props[propname] = []
                props[propname].append(value)

        for child in elem.getchildren():
            self.parse_item_props(child, props, ref)

    def parse_value(self, elem, ref, names):
        if elem.get("itemscope") is not None:
            item = {}
            self.store_cache(ref, names, item)
            return self.parse_item_elem(elem, item)

        # from http://dev.w3.org/html5/md/#values
        tag = elem.tag
        if tag == "meta":
            value = self.text(elem.get("content"))
        elif tag in self.src_tags:
            value = self.url(self.base, elem.get("src"))
        elif tag in self.href_tags:
            value = self.url(self.base, elem.get("href"))
        elif tag == "object":
            value = self.url(self.base, elem.get("data"))
        elif tag == "time" and "datetime" in elem.keys():
            value = self.datetime(elem.get("datetime"))
        else:
            value = self.text(self.to_text(elem))

        self.store_cache(ref, names, value)
        return value

    href_tags = ["a", "area", "link"]
    src_tags = ["audio", "embed", "iframe", "img", "source", "video"]

    def store_cache(self, ref, names, value):
        if ref and names:
            for name in names:
                if name not in self.cache[ref]:
                    self.cache[ref][name] = []
                self.cache[ref][name].append(value)
        return value

    def to_text(self, elem):
        ret = elem.text or ""
        for child in elem.getchildren():
            ret += self.to_text(child)
            ret += child.tail or ""
        return ret

    def elem_by_id(self, elem, a_id):
        if elem.get("id") == a_id:
            return elem
        for child in elem.getchildren():
            ret = self.elem_by_id(child, a_id)
            if ret is not None:
                return ret
        return None

    def find_base(self):
        if self.doc.tag != "html":
            return

        for head in self.doc.getchildren():
            if head.tag != "head":
                continue
            for base in head.getchildren():
                if base.tag != "base":
                    continue
                uri = base.get("href")
                if uri is not None:
                    self.base = urljoin(self.base, uri)
                    return


def get_file_items(html_file, types=None, uri=""):
    with open(html_file, "r") as f:
        return items(f.read(), types, uri)


def main(args=None):
    args = args or sys.argv[1:]
    return get_file_items(args[0]) if args else None


if __name__ == '__main__':
    from pprint import pprint
    pprint(main())
