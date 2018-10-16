#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.contentrendering.plastexpackages.extractors.html.processor import process_html_body

from nti.contentprocessing.content_utils import sent_tokenize
from nti.contentprocessing.content_utils import tokenize_content

logger = __import__('logging').getLogger(__name__)


class HTMLExtractor(object):

    def __init__(self, element, lang='en'):
        self.lang = lang
        self.number_paragraph = 0
        self.number_sidebar = 0
        self.number_sidebar_note = 0
        self.number_sidebar_caution = 0
        self.number_sidebar_warning = 0
        self.number_figure = 0
        self.number_table = 0
        self.number_ntiglossary = 0
        self.number_unordered_list = 0
        self.number_ordered_list = 0
        self.number_equation = 0
        self.glossaries = []
        self.figure_captions = []
        self.sidebar_notes = []
        self.sidebar_warnings = []
        self.sidebar_cautions = []

        self.element = element
        self.plain_text = process_html_body(element, self)
        self.number_sentence = self.total_number_of_sentences()
        self.number_word, self.unique_words = self.total_number_of_words()
        self.number_unique_word = len(self.unique_words)
        self.number_char = len(self.plain_text)
        self.number_non_whitespace_char = self.get_non_whitespace_character_length(self.plain_text)
        
        self.glossary_data = self.compute_list_statistic(self.glossaries)
        self.figure_data = self.compute_list_statistic(self.figure_captions)
        self.sidebar_note_data = self.compute_list_statistic(self.sidebar_notes)
        self.sidebar_warning_data = self.compute_list_statistic(self.sidebar_warnings)
        self.sidebar_caution_data = self.compute_list_statistic(self.sidebar_cautions)

    def total_number_of_words(self):
        words = tokenize_content(self.plain_text, self.lang)
        ##TODO : we may need to eliminate stopword and do stemming to find unique words
        unique_words = set(words)
        return len(words), unique_words

    def total_number_of_sentences(self):
        sentences = sent_tokenize(self.plain_text, self.lang)
        return len(sentences)

    def total_number_of_paragraph(self):
        return self.number_paragraph

    def get_non_whitespace_character_length(self, plain_text):
        nws = u''.join(plain_text.split())
        return len(nws)

    def compute_list_statistic(self, content_list):
        data = {}
        data['char_count'] = 0
        data['non_whitespace_char_count'] = 0
        words = []
        sentences = [] 
        for item in content_list:
            sentences += sent_tokenize(item)
            words += tokenize_content(item)
            data['char_count'] += len(item)
            data['non_whitespace_char_count'] += self.get_non_whitespace_character_length(item)
        data['word_count'] = len(words)
        data['sentence_count'] = len(sentences)
        return data


