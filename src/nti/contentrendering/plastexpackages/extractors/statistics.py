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

from collections import OrderedDict


@component.adapter(IRenderedBook)
@interface.implementer(IContentUnitStatistics)
class _ContentUnitStatistics(object):

    element_details = ('table', 'sidebar_caution', 'sidebar_warning', 'sidebar_note', 'figure', 'glossary')

    def __init__(self, unused_book=None, lang='en'):
        self.lang = lang
        self.index = OrderedDict()

    def transform(self, book, outpath=None):
        outpath = outpath or book.contentLocation
        # pylint: disable=attribute-defined-outside-init
        self.outpath = os.path.expanduser(outpath)
        target = os.path.join(outpath, 'content_metrics.json')
        dom = book.toc.dom
        root = dom.documentElement

        _ = self.process_topic(root)

        logger.info("Extracting content statistics to %s", target)
        with codecs.open(target, 'w', encoding='utf-8') as fp:
            json.dump(self.index,
                      fp,
                      indent='\t',
                      sort_keys=False,
                      ensure_ascii=True)

    def process_topic(self, node):
        unique_words = set()
        if node.hasAttribute('ntiid'):
            ntiid = node.getAttributeNode('ntiid').value
            href = node.getAttributeNode('href').value
            if u'#' not in href:
                html_element = self._read_html(href)
                extractor = HTMLExtractor(html_element, self.lang)
                unique_words = self._generate_metrics(ntiid, extractor)
            if node.hasChildNodes():
                for child in node.childNodes:
                    if child.nodeName == 'topic':
                        child_ntiid = child.getAttributeNode('ntiid').value
                        child_href = child.getAttributeNode('href').value
                        child_unique_words = self.process_topic(child)
                        if u'#' not in child_href:
                            self.roll_up_stats_to_parent(ntiid, child_ntiid)
                            unique_words = unique_words.union(child_unique_words)

            if u'#' not in href:
                self.compute_metrics(self.index[ntiid], unique_words)
        return unique_words

    def _generate_metrics(self, ntiid, extractor):
        self.index[ntiid] = {}
        self.index[ntiid]['paragraph_count'] = extractor.number_paragraph
        self.index[ntiid]['word_count'] = extractor.number_word
        self.index[ntiid]['sentence_count'] = extractor.number_sentence
        self.index[ntiid]['char_count'] = extractor.number_char
        self.index[ntiid]['non_whitespace_char_count'] = extractor.number_non_whitespace_char
        self.index[ntiid]['non_figure_image_count'] = extractor.number_non_figure_image
        self.index[ntiid]['unique_word_count'] = extractor.number_unique_word
        self.index[ntiid]['BlockElementDetails'] = {}
        self.create_block_element_details(self.index[ntiid]['BlockElementDetails'], extractor)
        unique_words = extractor.unique_words
        self.index[ntiid]['expected_consumption_time'] = extractor.expected_consumption_time
        return unique_words

    def roll_up_stats_to_parent(self, parent_ntiid, ntiid):
        self.index[parent_ntiid]['paragraph_count'] += self.index[ntiid]['paragraph_count']
        self.index[parent_ntiid]['non_figure_image_count'] += self.index[ntiid]['non_figure_image_count']
        self.accumulate_stat(self.index[parent_ntiid], self.index[ntiid])
        self.roll_up_block_element_details_stat(self.index[parent_ntiid]['BlockElementDetails'], self.index[ntiid]['BlockElementDetails'])

    def compute_metrics(self, element_index, unique_words):
        element_index['unique_word_count'] = len(unique_words)
        element_index['avg_word_per_sentence'] = self.try_div(element_index['word_count'], element_index['sentence_count'])
        element_index['avg_word_per_paragraph'] = self.try_div(element_index['word_count'], element_index['paragraph_count'])
        element_index['unique_percentage_of_word_count'] = self.try_div(element_index['unique_word_count'], element_index['word_count'])
        sorted_words = sorted(unique_words, key=len)
        element_index['length_of_the_shortest_word'] = len(sorted_words[0])
        element_index['length_of_the_longest_word'] = len(sorted_words[-1])
        self.compute_total_stat(element_index)

    def _read_html(self, name):
        filename = os.path.join(os.path.dirname(__file__), self.outpath, name)
        reader = HTMLReader(filename)
        element = reader.element
        return element

    def compute_total_stat(self, index):
        stats = ('char_count', 'non_whitespace_char_count', 'sentence_count', 'word_count')
        sub_index = index['BlockElementDetails']

        # intialize total_*
        for field in stats:
            tfield = 'total_%s' % field
            index[tfield] = index[field]

        for el in self.element_details:
            for field in stats:
                if field in sub_index[el]:
                    tfield = 'total_%s' % field
                    index[tfield] = index[tfield] + sub_index[el][field]

    def accumulate_stat(self, parent_dict, child_dict):
        parent_dict['char_count'] += child_dict['char_count']
        parent_dict['non_whitespace_char_count'] += child_dict['non_whitespace_char_count']
        parent_dict['sentence_count'] += child_dict['sentence_count']
        parent_dict['word_count'] += child_dict['word_count']

    def roll_up_block_element_details_stat(self, parent_dict, child_dict):
        for el in self.element_details:
            parent_dict[el]['count'] += child_dict[el]['count']
            self.accumulate_stat(parent_dict[el], child_dict[el])

    def create_block_element_details(self, index, extractor):
        for el in self.element_details:
            if el == 'table':
                self.sub_element_data(index, el, extractor.number_table, extractor.table_data)
            elif el == 'glossary':
                self.sub_element_data(index, el, extractor.number_ntiglossary, extractor.glossary_data)
            elif el == 'figure':
                self.sub_element_data(index, el, extractor.number_figure, extractor.figure_data)
            elif el == 'sidebar_caution':
                self.sub_element_data(index, el, extractor.number_sidebar_caution, extractor.sidebar_caution_data)
            elif el == 'sidebar_warning':
                self.sub_element_data(index, el, extractor.number_sidebar_warning, extractor.sidebar_warning_data)
            elif el == 'sidebar_note':
                self.sub_element_data(index, el, extractor.number_sidebar_note, extractor.sidebar_note_data)
            else:
                logger.warning('Unhandled element detail')

    def sub_element_data(self, index, el_name, count, data):
        index[el_name] = data
        index[el_name]['count'] = count

    def try_div(self, numerator, denominator):
        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0
