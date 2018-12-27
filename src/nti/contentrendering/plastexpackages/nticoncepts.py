#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from plasTeX import Command
from plasTeX import Environment


class concepthierarchy(Environment):
    blockType = True

    def invoke(self, tex):
        result = super(concepthierarchy, self).invoke(tex)

    class concept(Environment):
        blockType = True
        args = '<title:str:source>'

        class subconcept(Command):
            args = 'value:str'
            blockType = False
