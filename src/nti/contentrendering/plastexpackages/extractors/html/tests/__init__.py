#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

import unittest

from nti.contentrendering.tests import SharedConfiguringTestLayer
from nti.contentprocessing.content_utils import sent_tokenize
from nti.contentprocessing.content_utils import tokenize_content

class HTMLSample(object):
    def __init__(self):
        self.number_paragraph = 0
        self.number_sidebar = 0
        self.number_figure = 0
        self.number_table = 0
        self.number_ntiglossary = 0
        self.number_unordered_list = 0
        self.number_ordered_list = 0
        self.glossaries = list()

    def compute_glossary_statistic(self):
        data = {}
        data['number_of_char'] = 0
        words = []
        sentences = [] 
        for item in self.glossaries:
            sentences += sent_tokenize(item)
            words += tokenize_content(item)
            data['number_of_char'] += len(item)
        data['number_of_words'] = len(words)
        data['number_of_sentences'] = len(sentences)
        return data


class HTMLExtractorTests(unittest.TestCase):
    layer = SharedConfiguringTestLayer
