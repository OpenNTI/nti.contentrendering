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

    def compute_list_statistic(self, content_list):
        data = {}
        data['char_count'] = 0
        words = []
        sentences = [] 
        for item in content_list:
            sentences += sent_tokenize(item)
            words += tokenize_content(item)
            data['char_count'] += len(item)
        data['word_count'] = len(words)
        data['sentence_count'] = len(sentences)
        return data


class HTMLExtractorTests(unittest.TestCase):
    layer = SharedConfiguringTestLayer
