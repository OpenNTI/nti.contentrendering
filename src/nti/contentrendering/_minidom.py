#!/usr/bin/env python
"""
Utilities for working with :mod:`xml.dom.minidom` objects.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import io

from nti.contentprocessing._compat import text_


def minidom_writexml(document, outfile, encoding=u'utf-8'):
    """
    Papers over some very bad Unicode issues
    that crop up with xml.dom.minidom.
    """
    class _StupidIOPackageCannotDealWithBothStrAndUnicodeObjects(object):

        def __init__(self, under):
            self._under = under

        def write(self, x):
            if isinstance(x, str):
                x = text_(x)
            self._under.write(x)

    with io.open(outfile, "w", encoding=encoding) as f:
        document.writexml(_StupidIOPackageCannotDealWithBothStrAndUnicodeObjects(f),
                          encoding=encoding)
