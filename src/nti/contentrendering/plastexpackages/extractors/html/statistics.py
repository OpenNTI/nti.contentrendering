#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader
from nti.contentrendering.plastexpackages.extractors.html.processor import process_html_body

from nti.contentprocessing import default_word_tokenizer_expression

from nti.contentprocessing.tokenizer.tokenizer import SpaceTokenizer
from nti.contentprocessing.tokenizer.tokenizer import DefaultRegexpTokenizer


class HTMLExtractor(object):
	def __init__(self, element):
		self.number_paragraph = 0
		self.number_sidebar = 0
		self.element = element
		self.plain_text = process_html_body(element, self)
		

	def total_number_of_words(self):
		tokenizer = DefaultRegexpTokenizer(default_word_tokenizer_expression)
		words = tokenizer.tokenize(self.plain_text)
		return len(words)

	def total_number_of_sentences(self, plain_text):
		pass

	def total_number_of_paragraph(self):
		return self.number_paragraph



