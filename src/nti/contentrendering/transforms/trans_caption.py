#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentrendering.interfaces import IDocumentTransformer


def transform(document):
    # For includegraphics, ntiincludeannotationgraphics, and
    # ntiincludenoannotationgraphics we do not want caption object to
    # be displayed since the information is presented in a different
    # manner.
    for caption in document.getElementsByTagName('caption') or ():
        parent = caption.parentNode
        if len(parent.getElementsByTagName('ntiincludeannotationgraphics')):
            caption.style['display'] = 'none'
        elif len(parent.getElementsByTagName('ntiincludenoannotationgraphics')):
            caption.style['display'] = 'none'
        elif len(parent.getElementsByTagName('includegraphics')):
            caption.style['display'] = 'none'

from zope import interface
interface.moduleProvides(IDocumentTransformer)
