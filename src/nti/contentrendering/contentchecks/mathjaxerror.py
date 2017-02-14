#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from lxml import etree

from zope import interface

from nti.contentrendering.interfaces import IRenderedBookValidator
interface.moduleProvides(IRenderedBookValidator)

etree_tostring = getattr(etree, 'tostring')


def check(book):

    def _report_errors(errors, page, text='xml'):
        all_errors = len(errors)
        if all_errors:
            errors = set(etree_tostring(e, method=text) for e in errors)
            logger.warn("Mathjax errors for page %s: %s",
                        page.filename,
                          errors)
        return all_errors

    def _check_merror(page):
        errors = page.dom("span[class=merror]")
        return _report_errors(errors, page)

    def _check_mtext(page):
        mtexts = page.dom("span[class=mtext]")
        errors = []
        for mtext in mtexts:
            if         'style' in mtext.attrib \
                and 'color:' in mtext.attrib['style'] \
                and 'red' in mtext.attrib['style']:
                # This is a really tacky way of checking for 'color: red'
                errors.append(mtext)
        return _report_errors(errors, page, text='text')

    def _check(page):
        all_errors = _check_merror(page)
        all_errors += _check_mtext(page)
        for child in page.childTopics or ():
            all_errors += _check(child)
        return all_errors

    all_errors = _check(book.toc.root_topic)
    if not all_errors:
        logger.info("No MathJax errors")
    return all_errors
