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
    text = []
    process_element(text, body, html)
    return u''.join(text)


def check_element_text(text, element):
    if element.text:
        text.append(element.text)


def check_child(text, element, html=None):
    for child in element:
        if child.tag == 'br':
            text.append('\n')
        elif child.tag == 'p':
            process_paragraph(text, child, html)
        elif child.tag == 'div':
            process_div(text, child, html)
        elif child.tag == 'img':
            if html:
                html.number_non_figure_image += 1  # it does not include under <div class="figure">
        elif child.tag == 'realpagenumber':
            pass
        elif child.tag == 'a':
            process_anchor(text, child, html)
        elif child.tag == 'ul':
            process_element(text, child, html)
            if html:
                html.number_unordered_list += 1
        elif child.tag == 'ol':
            process_element(text, child, html)
            if html:
                html.number_ordered_list += 1
        elif child.tag == 'li':
            temp = []
            process_element(temp, child, html)
            text.append(child.text_content().strip())
            text.append('\n')
        elif child.tag == 'expectedconsumptiontime':
            if 'value' in child.attrib:
                html.expected_consumption_time = float(child.attrib['value'])
        else:
            process_element(text, child, html)


def check_element_tail(text, element):
    if element.tail:
        text.append(element.tail)


def process_element(text, element, html=None):
    check_element_text(text, element)
    check_child(text, element, html)
    check_element_tail(text, element)


def process_paragraph(text, element, html=None):
    new_text = []
    process_element(new_text, element, html)
    new_texts = u''.join(new_text)
    if 'class' in element.attrib:
        if html and element.attrib['class'] == 'par' and element.getparent().tag != 'li':
            if not new_texts.isspace():
                html.number_paragraph = html.number_paragraph + 1
    if not new_texts.isspace():
        text.append(new_texts.strip())
        text.append('\n')


DIV_CLASS_TITLE = ('chapter title', 'section title', 'subsection title')


def process_div(text, element, html=None):
    current_number_paragraph = html.number_paragraph
    if 'class' in element.attrib:
        if element.attrib['class'] in DIV_CLASS_TITLE or element.attrib['class'] == 'sidebar title':
            new_text = []
            process_element(new_text, element, html)
            new_texts = u''.join(new_text)
            text.append(new_texts.strip())
            text.append('\n')
        elif element.attrib['class'] == 'sidebar':
            process_element(text, element, html)
            if html:
                html.number_sidebar += 1
                # need to discuss whether we want to count paragraph inside a
                # sidebar
                if current_number_paragraph == html.number_paragraph:
                    html.number_paragraph += 1
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
                html.number_equation += 1
        else:
            process_element(text, element, html)
    else:
        process_element(text, element, html)


def process_anchor(text, element, html=None):
    if 'class' in element.attrib:
        if element.attrib['class'] == 'ntiglossaryentry':
            html.number_ntiglossary += 1
    process_element(text, element, html)
