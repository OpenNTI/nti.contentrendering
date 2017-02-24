#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX.Base.LaTeX.Lists import List
from plasTeX.Base.LaTeX.Lists import itemize
from plasTeX.Base.LaTeX.Lists import trivlist
from plasTeX.Base.LaTeX.Lists import enumerate_


class ntilist(List):
    macroName = 'ntilist'


class ntiitemize(itemize):
    macroName = 'ntiitemize'


class ntienumerate(enumerate_):
    macroName = 'ntienumerate'


class ntitrivlist(trivlist):
    macroName = 'ntitrivlist'


class ntinavlist(List):
    pass
