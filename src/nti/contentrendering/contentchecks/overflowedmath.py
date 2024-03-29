#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import interface

from nti.contentrendering.interfaces import IRenderedBookValidator
interface.moduleProvides(IRenderedBookValidator)

from nti.contentrendering import javascript_path
javascript = javascript_path('detectOverflowedMath.js')


def check(book):
    start = time.time()
    pagesWithBadMath = 0
    results = book.runPhantomOnPages(javascript)
    for (ntiid, _, _), maths in results.items():
        page = book.pages[ntiid]
        if maths:
            pagesWithBadMath += 1
            logger.warn('Width of math elements %s is outside the bounds of %s.',
                        maths, page.filename)

    if pagesWithBadMath == 0:
        logger.info('All math within page bounds')

    logger.info("overflowed math checked in %s(s)", 
                 time.time() - start)
