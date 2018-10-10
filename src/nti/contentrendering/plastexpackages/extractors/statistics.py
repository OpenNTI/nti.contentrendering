#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract content unit statistics

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

import codecs

import simplejson as json

from zope import component
from zope import interface

from nti.contentrendering.interfaces import IRenderedBook
from nti.contentrendering.interfaces import IContentUnitStatistics

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

from nti.contentrendering.plastexpackages.extractors.html.statistics import HTMLExtractor

logger = __import__('logging').getLogger(__name__)


@component.adapter(IRenderedBook)
@interface.implementer(IContentUnitStatistics)
class _ContentUnitStatistics(object):

    def __init__(self, unused_book=None, lang='en'):
        self.lang = lang

    def transform(self, book, outpath=None):
        outpath = outpath or book.contentLocation
        # pylint: disable=attribute-defined-outside-init
        self.outpath = os.path.expanduser(outpath)
        target = os.path.join(outpath, 'content_index.json')
        dom = book.toc.dom
        root = dom.documentElement
        index = {'Items': {}}
        self._process_topic(root, index['Items'])

        logger.info("Extracting content statistics to %s", target)
        with codecs.open(target, 'w', encoding='utf-8') as fp:
            json.dump(index,
                      fp,
                      indent='\t',
                      sort_keys=True,
                      ensure_ascii=True)
        return index

    def _process_topic(self, node, index):
        unique_words = set()
        if node.hasAttribute('ntiid'):
            ntiid = node.getAttributeNode('ntiid').value
            element_index = index[ntiid] = {}
            element_index['NTIID'] = ntiid
            element_index['href'] = node.getAttributeNode('href').value
            if u'#' not in element_index['href']:
                html_element = self._read_html(element_index['href'])
                extractor = HTMLExtractor(html_element, self.lang)
                element_index['number_of_paragraphs'] = extractor.number_paragraph
                element_index['number_of_words'] = extractor.number_word
                element_index['number_of_sentences'] = extractor.number_sentence
                element_index['number_of_unique_words'] = extractor.number_unique_word
                element_index['number_of_chars'] = extractor.number_char
                element_index['number_of_non_whitespace_chars'] = extractor.number_non_whitespace_char
                element_index['number_of_table'] = extractor.number_table 
                element_index['number_of_sidebar'] = extractor.number_sidebar 
                element_index['number_of_ntiglossary'] = extractor.number_ntiglossary 
                element_index['number_of_ordered_list'] = extractor.number_ordered_list
                element_index['number_of_unordered_list'] = extractor.number_unordered_list
                unique_words = extractor.unique_words

        if node.hasChildNodes():
            for child in node.childNodes:
                if child.nodeName == 'topic':
                    containing_index = element_index.setdefault('Items', {})
                    child_unique_words = self._process_topic(child, containing_index)
                    child_ntiid = child.getAttributeNode('ntiid').value
                    if u'#' not in containing_index[child_ntiid]['href']:
                        element_index['number_of_paragraphs'] += containing_index[child_ntiid]['number_of_paragraphs']
                        element_index['number_of_sentences'] += containing_index[child_ntiid]['number_of_sentences']
                        element_index['number_of_words'] += containing_index[child_ntiid]['number_of_words']
                        element_index['number_of_chars'] += containing_index[child_ntiid]['number_of_chars']
                        element_index['number_of_non_whitespace_chars'] += containing_index[child_ntiid]['number_of_non_whitespace_chars']
                        element_index['number_of_table'] += containing_index[child_ntiid]['number_of_table']
                        element_index['number_of_sidebar'] += containing_index[child_ntiid]['number_of_sidebar']
                        element_index['number_of_ntiglossary'] += containing_index[child_ntiid]['number_of_ntiglossary']
                        element_index['number_of_unordered_list'] += containing_index[child_ntiid]['number_of_unordered_list']
                        element_index['number_of_ordered_list'] += containing_index[child_ntiid]['number_of_ordered_list']
                        unique_words = unique_words.union(child_unique_words)
        
        if node.hasAttribute('ntiid') and u'#' not in element_index['href']:
            element_index['number_of_unique_words'] = len(unique_words)
            element_index['avg_word_per_sentence'] = element_index['number_of_words']/element_index['number_of_sentences']
            element_index['avg_word_per_paragraph']  = element_index['number_of_words']/element_index['number_of_paragraphs']
            element_index['unique_percentage_of_words'] = element_index['number_of_unique_words']/element_index['number_of_words']   
            sorted_words = sorted(unique_words, key=len)
            element_index['length_of_the_shortest_word'] = len(sorted_words[0]) 
            element_index['length_of_the_longest_word'] = len(sorted_words[-1]) 
        return unique_words

    def _read_html(self, name):
        filename = os.path.join(os.path.dirname(__file__), self.outpath, name)
        reader = HTMLReader(filename)
        element = reader.element
        return element
