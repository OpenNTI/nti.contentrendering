#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CMU macros

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX.Base import chapter
from plasTeX.Base import Command
from plasTeX.Base import paragraph
from plasTeX.Base import ColumnType
from plasTeX.Base import Environment
from plasTeX.Base import DimenCommand
from plasTeX.Base.FontSelection import TextCommand


class _Ignored(Command):
    unicode = ''

    def invoke(self, tex):
        return []


class lecture(chapter):
    args = '* [shorttitle] title { label }'


# Parse the frame environment and \frametitle as if it was a \paragraph element
class frametitle(paragraph):
    pass


# Parses the \frame environment and produces no output.  The childred of
# this environment print as if they were not inside the frame environment.
class frame(Environment):

    args = ' {title:str} [unknown:str]'

    def invoke(self, tex):
        self.parse(tex)
        return []


# Parses the \columns environment and produces no output.  The childred of
# this environment print as if they were not inside the solumns environment.
class columns(Environment):
    args = '[ pos:str ]'

    def invoke(self, tex):
        self.parse(tex)
        return []


class column(Command):
    args = '[ pos:str ] width:int'

    def invoke(self, tex):
        self.parse(tex)
        return []


class framebreak(_Ignored):
    pass


class noframebreak(_Ignored):
    pass


class mtiny(Command):
    pass


class pause(Command):
    pass


class alert(TextCommand):
    args = '< overlay > self'


class colortabular(Environment):
    pass


class contentwidth(DimenCommand):
    value = DimenCommand.new('600pt')


class beamertemplatebookbibitems(_Ignored):
    pass


class beamertemplatearticlebibitems(_Ignored):
    pass


class alt(Command):
    args = '< overlay > default alternative'


# Custom column type for CMU tables
ColumnType.new(str('Y'), {'text-align': 'left'})

ColumnType.new(str('k'),
               {'text-align': 'left', 'background-color': '#cccccc'},
               args='width:str')


# Custom command to for title row color
class titlerow(Command):
    args = '[ space ]'

    def digest(self, tokens):
        super(titlerow, self).digest(tokens)
        node = self.parentNode.parentNode
        node.rowspec['background-color'] = '#cccccc'


# Custom commands for use with the algorithm2e environment
class Label(Command):
    args = 'self'
    blockType = True


class Goto(Command):
    args = 'self'
    blockType = True


class Procedure(Command):
    args = 'self'
    blockType = True


class Input(Command):
    args = 'self'
    blockType = True
