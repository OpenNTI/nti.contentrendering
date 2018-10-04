#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLExtractorTests

from lxml import html


from nti.contentrendering.plastexpackages.extractors.html.processor import process_element

class HTMLSample(object):
	number_paragraph = 0

class HTMLProcessTest(HTMLExtractorTests):
	def test_simple_paragraph(self):
		script = """<body><div><p class="par" id="cea4cf4b4bfca0e0912c8b9308ae9c64">We recommend the following specifications to ensure the highest quality experience while using NextThought: </p></div></body>"""
		element = html.fromstring(script)
		text = ""
		text = process_element(text, element)
		assert_that(text, is_(u'We recommend the following specifications to ensure the highest quality experience while using NextThought: \n'))

	def test_bolded_paragraph(self):
		script = """<body><div><p class="par" id="ac446671f9623e95ea098e5d0777dc39"><b class="bfseries">Can everyone see the note I just made?</b><br /></p></div></body>"""
		element = html.fromstring(script)
		text = ""
		text = process_element(text, element)
		assert_that(text, is_(u'Can everyone see the note I just made?\n\n'))

	def test_bolded_paragraph_with_tail(self):
		script = """<body><div><p class="par" id="ac446671f9623e95ea098e5d0777dc39"><b class="bfseries">Can everyone see the note I just made?</b> This is a tail<br /></p></div></body>"""
		element = html.fromstring(script)
		text = ""
		text = process_element(text, element)
		assert_that(text, is_(u'Can everyone see the note I just made? This is a tail\n\n'))

	def test_paragraph(self):
		script = """<body><div class="section title">System Requirements</div> <p class="placeholder"></p> <p class="par"> <a name="section:System Requirements"></a> </p> <a name="cea4cf4b4bfca0e0912c8b9308ae9c64"></a> <p class="par" id="cea4cf4b4bfca0e0912c8b9308ae9c64">We recommend the following specifications to ensure the highest quality experience while using NextThought: </p> <a name="45bb5b2ce7b3402678006a7b9b89c5e8"></a> <p class="par" id="45bb5b2ce7b3402678006a7b9b89c5e8">1Mb/s+ broadband Internet connection for optimal video viewing A computer with at least 2GB memory and minimum screen resolution of 1024x768 <a href="http://get.adobe.com/reader/">Adobe Reader</a> or similar PDF reading software </p> </div></body>"""
		element = html.fromstring(script)
		text = ""
		html_obj = HTMLSample()
		text = process_element(text, element, html_obj)
		assert_that(html_obj.number_paragraph, is_(2))
		assert_that(text, is_(u'System Requirements\n \nWe recommend the following specifications to ensure the highest quality experience while using NextThought: \n1Mb/s+ broadband Internet connection for optimal video viewing A computer with at least 2GB memory and minimum screen resolution of 1024x768 Adobe Reader or similar PDF reading software \n'))









