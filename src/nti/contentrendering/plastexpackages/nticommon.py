#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX import Command


class ntidescription(Command):
    """
    Command to add descriptions to some NTI objects
    """
    args = 'content:str:source'
