#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from plasTeX.Renderers import render_children

logger = __import__('logging').getLogger(__name__)


def _render_children(renderer, nodes, strip=False):
    if not isinstance(nodes, six.string_types):
        result = u''.join(render_children(renderer, nodes))
    else:
        result = nodes.decode("utf-8") if isinstance(nodes, bytes) else nodes
    result = result.strip() if strip and result else result
    return result


def _render_elemet(element, strip=False):
    return _render_children(element.renderer, element, strip)
