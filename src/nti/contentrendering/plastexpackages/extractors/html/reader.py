#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import codecs

from lxml import html

logger = __import__('logging').getLogger(__name__)


class HTMLReader(object):

    def __init__(self, inputfile):
        self.inputfile = inputfile
        self.script = self.get_script()
        self.element = html.fromstring(self.script)

    def get_script(self):
        script = None
        # verify that the input file exists
        inputfile = os.path.expanduser(self.inputfile)
        if not os.path.exists(inputfile):
            logger.warning('The source file %s does not exist',  inputfile)
        else:
            with codecs.open(inputfile, 'r', 'utf-8') as fp:
                script = fp.read()
        return script
