#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

logger = __import__('logging').getLogger(__name__)

from plasTeX import Command


class expectedconsumptiontime(Command):
    args = 'time:str'
    blockType = False
