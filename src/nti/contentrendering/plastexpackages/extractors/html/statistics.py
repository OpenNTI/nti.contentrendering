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
        self.number_of_figure = 0
        self.element = element
        self.plain_text = process_html_body(element, self)
        self.number_sentence = self.total_number_of_sentences()
        self.number_word, self.number_unique_word = self.total_number_of_words()

    def total_number_of_words(self):
        words = tokenize_content(self.plain_text, self.lang)
        unique_words = set(words)
        return len(words), len(unique_words)

    def total_number_of_sentences(self):
        sentences = sent_tokenize(self.plain_text, self.lang)
        return len(sentences)

    def total_number_of_paragraph(self):
        return self.number_paragraph
