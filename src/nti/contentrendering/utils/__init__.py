# -*- coding: utf-8 -*-
"""
Content rendering utils module

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentrendering.utils.chameleon import setupChameleonCache

from nti.contentrendering.utils.rendered_book import EmptyMockDocument
from nti.contentrendering.utils.rendered_book import NoPhantomRenderedBook
from nti.contentrendering.utils.rendered_book import NoConcurrentPhantomRenderedBook

from nti.contentrendering.utils.rendered_book import _phantom_function
