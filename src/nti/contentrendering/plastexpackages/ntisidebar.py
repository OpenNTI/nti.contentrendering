#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from plasTeX import Command
from plasTeX import Environment

from nti.contentrendering import plastexids

logger = __import__('logging').getLogger(__name__)

# The sidebar environment is to be the base class for other side types
# such as those from AoPS.


class sidebarname(Command):
    unicode = ''

    def __delitem__(self, i):
        raise NotImplementedError


class sidebar(Environment, plastexids.NTIIDMixin):
    args = '[options:dict] title'
    blockType = True

    counter = 'sidebar'

    _ntiid_suffix = u'sidebar.'
    _ntiid_title_attr_name = 'title'
    _ntiid_type = u'HTML:NTISidebar'
    _ntiid_allow_missing_title = True
    _ntiid_cache_map_name = '_sidebar_ntiid_map'

    embedded_doc_cross_ref_url = property(plastexids._embedded_node_cross_ref_url)

    @property
    def css_class(self):
        try:
            return ' '.join([type(self).__name__, self._options.get('css-class')])
        except (AttributeError, KeyError):
            return type(self).__name__

    def invoke(self, tex):
        result = super(sidebar, self).invoke(tex)
        # pylint: disable=attribute-defined-outside-init
        self._options = self.attributes.get('options', {})
        return result

    def __delitem__(self, i):
        raise NotImplementedError


class flatsidebar(sidebar):

    def __delitem__(self, i):
        raise NotImplementedError


class audiosidebar(sidebar):
    args = 'audioref'

    def __delitem__(self, i):
        raise NotImplementedError

class ntigraphicsidebar(sidebar):
    args = 'title graphic_class:str:source'

    def __delitem__(self, i):
        raise NotImplementedError
