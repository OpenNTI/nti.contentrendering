#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Adapters and utilities used for traversing objects used during the
content rendering process.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.location.interfaces import LocationError

from zope.traversing.adapters import DefaultTraversable

logger = __import__('logging').getLogger(__name__)


class PlastexTraverser(DefaultTraversable):
    """
    Missing attributes simply return None. Many existing templates
    rely on this (instead of specifying a default fallback) since
    the plastex simple-tal engine had this behaviour.

    This MUST be registered as an adapter for the DOM objects
    used in rendering.
    """

    def traverse(self, name, furtherPath):
        try:
            return super(PlastexTraverser, self).traverse(name, furtherPath)
        except (LocationError, IndexError) as e:
            # Warning !!! This can mask issues.
            logger.warning('Traversal error while rendering (%s) (%s)',
                           name, e)
            # IndexError can be raised because the plasTeX objects attempt
            # to use strings as child numbers
            return None
