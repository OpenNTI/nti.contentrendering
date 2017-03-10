#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX.Base import chapter
from plasTeX.Base import section
from plasTeX.Base import subsection
from plasTeX.Base import subsubsection


class litclubsession(chapter):
    pass


class litclubsessionsection(section):
    pass


class litclubsection(subsection):
    pass


class litclubsubsection(subsubsection):
    pass


class litclubwelcomesection(section):
    pass


class litclubhellosongsubsection(subsubsection):
    pass


class litclubcheckinsubsection(subsubsection):
    pass


class litclubcommunitysection(section):
    pass


class litclubreadaloudsection(section):
    pass


class litclubdiscussionsubsection(subsubsection):
    pass


class litclubcoresection(section):
    pass


class litclubindereadingsection(subsection):
    pass


class litclubwrapupsection(section):
    pass


class litclubpraisesubsection(subsubsection):
    pass


class litclubgoodbyesongsubsection(subsubsection):
    pass
