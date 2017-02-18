#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from plasTeX.Renderers import render_children

from nti.contentprocessing._compat import unicode_


def _render_children(renderer, nodes, strip=False):
    if not isinstance(nodes, six.string_types):
        result = unicode_(''.join(render_children(renderer, nodes)))
    else:
        result = nodes.decode("utf-8") if isinstance(nodes, bytes) else nodes
    result = result.strip() if strip and result else result
    return result


def _render_elemet(element, strip=False):
    return _render_children(element.renderer, element, strip)
