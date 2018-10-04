#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def check_element_text(text, element):
    if element.text:
        text = text + element.text
    return text

def check_child(text, element, html=None):
    for child in element:
        if child.tag == 'br':
            text = text + '\n'
        elif child.tag == 'p':
            text = process_paragraph(text, child, html)
        else:
            text = process_element(text, child, html)
    return text

def check_element_tail(text, element):
    if element.tail:
        if not element.tail.isspace():
            text = text + element.tail
    return text

def process_element(text, element, html=None):
    text = check_element_text(text, element)
    text = check_child(text, element, html)
    text = check_element_tail(text, element)
    return text

def process_paragraph(text, element, html=None):
    if 'id' in element.attrib and 'class' in element.attrib:
        if html and element.attrib['class'] == 'par':
            html.number_paragraph = html.number_paragraph + 1
    text = process_element(text, element, html)
    text = text + '\n'
    return text