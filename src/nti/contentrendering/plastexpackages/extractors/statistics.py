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
                element_index['number_of_tables'] = extractor.number_table 
                element_index['number_of_sidebars'] = extractor.number_sidebar 
                element_index['number_of_ntiglossary'] = extractor.number_ntiglossary 
                element_index['number_of_ordered_list'] = extractor.number_ordered_list
                element_index['number_of_unordered_list'] = extractor.number_unordered_list
                element_index['number_of_figures'] = extractor.number_figure
                element_index['number_of_sidebar_notes'] = extractor.number_sidebar_note 
                element_index['number_of_sidebar_warnings'] = extractor.number_sidebar_warning 
                element_index['number_of_sidebar_cautions'] = extractor.number_sidebar_caution 
                element_index['number_of_equations'] = extractor.number_equation
                element_index['figure_stats'] = extractor.figure_data
                element_index['glossary_stats'] = extractor.glossary_data
                element_index['sidebar_note_stats'] = extractor.sidebar_note_data
                element_index['sidebar_warning_stats'] = extractor.sidebar_warning_data
                element_index['sidebar_caution_stats'] = extractor.sidebar_caution_data
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
                        element_index['number_of_tables'] += containing_index[child_ntiid]['number_of_tables']
                        element_index['number_of_sidebars'] += containing_index[child_ntiid]['number_of_sidebars']
                        element_index['number_of_ntiglossary'] += containing_index[child_ntiid]['number_of_ntiglossary']
                        element_index['number_of_unordered_list'] += containing_index[child_ntiid]['number_of_unordered_list']
                        element_index['number_of_ordered_list'] += containing_index[child_ntiid]['number_of_ordered_list']
                        element_index['number_of_figures'] += containing_index[child_ntiid]['number_of_figures']
                        element_index['number_of_sidebar_notes'] += containing_index[child_ntiid]['number_of_sidebar_notes']
                        element_index['number_of_sidebar_warnings'] += containing_index[child_ntiid]['number_of_sidebar_warnings']
                        element_index['number_of_sidebar_cautions'] += containing_index[child_ntiid]['number_of_sidebar_cautions']
                        element_index['number_of_equations'] += containing_index[child_ntiid]['number_of_equations']
                        self.accumulate_stat(element_index['figure_stats'], containing_index[child_ntiid]['figure_stats'])
                        self.accumulate_stat(element_index['glossary_stats'], containing_index[child_ntiid]['glossary_stats'])
                        self.accumulate_stat(element_index['sidebar_note_stats'], containing_index[child_ntiid]['sidebar_note_stats'])
                        self.accumulate_stat(element_index['sidebar_warning_stats'], containing_index[child_ntiid]['sidebar_warning_stats'])
                        self.accumulate_stat(element_index['sidebar_caution_stats'], containing_index[child_ntiid]['sidebar_caution_stats'])
                        unique_words = unique_words.union(child_unique_words)
        
        if node.hasAttribute('ntiid') and u'#' not in element_index['href']:
            element_index['number_of_unique_words'] = len(unique_words)
            element_index['avg_word_per_sentence'] = self.try_div(element_index['number_of_words'],element_index['number_of_sentences'])
            element_index['avg_word_per_paragraph'] = self.try_div(element_index['number_of_words'],element_index['number_of_paragraphs'])
            element_index['unique_percentage_of_words'] = self.try_div(element_index['number_of_unique_words'],element_index['number_of_words'])
            sorted_words = sorted(unique_words, key=len)
            element_index['length_of_the_shortest_word'] = len(sorted_words[0]) 
            element_index['length_of_the_longest_word'] = len(sorted_words[-1]) 
        return unique_words

    def _read_html(self, name):
        filename = os.path.join(os.path.dirname(__file__), self.outpath, name)
        reader = HTMLReader(filename)
        element = reader.element
        return element

    def accumulate_stat(self, parent_dict, child_dict):
        parent_dict['number_of_chars'] += child_dict['number_of_chars']
        parent_dict['number_of_non_whitespace_chars'] += child_dict['number_of_non_whitespace_chars']
        parent_dict['number_of_sentences'] += child_dict['number_of_sentences']
        parent_dict['number_of_words'] += child_dict['number_of_words']

    def try_div(self, numerator, denominator):
        try: return numerator/denominator
        except ZeroDivisionError: return 0
