#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)


def process_html_body(element, html=None):
    body = element.find('body')
    text = process_element(u'', body, html)
    return text


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
        elif child.tag == 'img':
            pass
        elif child.tag == 'realpagenumber':
            pass
        elif child.tag == 'a':
            text = process_anchor(text, child, html)
        elif child.tag == 'ul':
            text = process_element(text, child, html)
            if html:
                html.number_unordered_list += 1
        elif child.tag == 'ol':
            text = process_element(text, child, html)
            if html:
                html.number_ordered_list += 1
        elif child.tag == 'li':
            text = process_element(text, child, html)
            text = text.strip() + '\n'
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
    new_text = process_element(u"", element, html)
    if 'class' in element.attrib:
        if html and element.attrib['class'] == 'par':
            if not new_text.isspace():
                html.number_paragraph = html.number_paragraph + 1
    text = text + new_text + u'\n'
    return text


def process_div(text, element, html=None):
    current_number_paragraph = html.number_paragraph
    if 'class' in element.attrib:
        if element.attrib['class'] == 'section title' or element.attrib['class'] == 'sidebar title':
            new_text = process_element(u"", element, html)
            text = text + new_text + u'\n'
        elif element.attrib['class'] == 'sidebar':
            new_text = process_element(u"", element, html)
            if html:
                html.number_sidebar += 1
                # need to discuss whether we want to count paragraph inside a
                # sidebar
                if current_number_paragraph == html.number_paragraph:
                    html.number_paragraph += 1
            text = text + new_text
        elif element.attrib['class'] == 'sidebar note':
            if html:
                html.number_sidebar_note += 1
                html.sidebar_notes.append(element.text_content().strip())
        elif element.attrib['class'] == 'sidebar warning':
            if html:
                html.number_sidebar_warning += 1
                html.sidebar_warnings.append(element.text_content().strip())
        elif element.attrib['class'] == 'sidebar caution':
            if html:
                html.number_sidebar_caution += 1
                html.sidebar_cautions.append(element.text_content().strip())
        elif element.attrib['class'] == 'figure':
            if html:
                html.number_figure += 1
                html.figure_captions.append(element.text_content().strip())
        elif element.attrib['class'] == 'glossary':
            ol = element.getchildren()[0]
            if html and ol.tag == 'ol':
                for li in ol:
                    span = li.getchildren()[0]
                    html.glossaries.append(span.text_content().strip())
        elif element.attrib['class'] == 'table':
            if html:
                html.number_table += 1
                html.tables.append(element.text_content().strip())
        elif element.attrib['class'] == 'math equation':
            if html:
                html.number_equation +=1
        else:
            text = process_element(text, element, html)
    else:
        text = process_element(text, element, html)
    return text

def process_anchor(text, element, html=None):
    if 'class' in element.attrib:
        if element.attrib['class'] == 'ntiglossaryentry':
            html.number_ntiglossary += 1
    text = process_element(text, element, html)
    return text
