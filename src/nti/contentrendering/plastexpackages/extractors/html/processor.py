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
        elif child.tag == 'div':
            text = process_div(text, child, html)
        else:
            text = process_element(text, child, html)
    return text

def check_element_tail(text, element):
    if element.tail:
        text = text + element.tail
    return text

def process_element(text, element, html=None):
    text = check_element_text(text, element)
    text = check_child(text, element, html)
    text = check_element_tail(text, element)
    return text

def process_paragraph(text, element, html=None):
    new_text = ""
    new_text = process_element(new_text, element, html)
    if 'class' in element.attrib:
        if html and element.attrib['class'] == 'par':
            if 'id' in element.attrib:
                html.number_paragraph = html.number_paragraph + 1
            else:
                if not new_text.isspace():
                    html.number_paragraph = html.number_paragraph + 1   
    text = text + new_text + '\n'
    return text

def process_div(text, element, html=None):
    current_number_paragraph = html.number_paragraph
    text = process_element(text, element, html)
    if 'class' in element.attrib:
        if element.attrib['class'] == 'section title' or element.attrib['class'] == 'sidebar title':
            text = text + '\n'
        if element.attrib['class'] == 'sidebar':
            if html:
                html.number_sidebar += 1
                ##need to discuss whether we want to count paragraph inside a sidebar
                if current_number_paragraph == html.number_paragraph:
                    html.number_paragraph += 1
    return text