#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

## re-export
from .phantom import _closing
from .phantom import javascript_path
from .phantom import run_phantom_on_page
from .phantom import _PhantomProducedUnexpectedOutputError

## BWC re-export
from nti.futures.futures import ConcurrentExecutor
ConcurrentExecutor = ConcurrentExecutor 
