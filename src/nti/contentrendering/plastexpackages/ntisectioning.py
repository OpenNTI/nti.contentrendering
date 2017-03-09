# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX.Base import Crossref

from plasTeX.Base.LaTeX.Sectioning import part
from plasTeX.Base.LaTeX.Sectioning import chapter
from plasTeX.Base.LaTeX.Sectioning import section
from plasTeX.Base.LaTeX.Sectioning import subsection
from plasTeX.Base.LaTeX.Sectioning import subsubsection


class titlelesspart(part):
    _ntiid_title_attr_name = u''
    _ntiid_allow_missing_title = True
ntititlelesspart = titlelesspart


class titlelesschapter(chapter):
    _ntiid_title_attr_name = u''
    _ntiid_allow_missing_title = True
ntititlelesschapter = titlelesschapter


class titlelesssection(section):
    _ntiid_title_attr_name = u''
    _ntiid_allow_missing_title = True
ntititlelesssection = titlelesssection


class titlelesssubsection(subsection):
    _ntiid_title_attr_name = u''
    _ntiid_allow_missing_title = True
ntititlelessubsection = titlelesssubsection


class ntititlelesssubsubsection(subsubsection):
    _ntiid_title_attr_name = u''
    _ntiid_allow_missing_title = True
titlelesssubsubsection = ntititlelesssubsubsection


# SAJ: Sectioning commands for custom rendering treatment
class chaptertitlesuppressed(chapter):
    pass


class sectiontitlesuppressed(section):
    pass


# TODO: do pagerefs even make sense in our dom?
# Try to find an intelligent page name for the reference
# so we don't have to render the link text as '3'
class pageref(Crossref.pageref):
    # we would hope to generate the pagename attribute in
    # the invoke method but since it is dependent on the page
    # splits used at render time we define a function to be called
    # from the page template

    def getPageNameForRef(self):
        # Look up the dom tree until we find something
        # that would create a file
        fileNode = self.idref['label']
        while     not getattr(fileNode, 'title', None) \
              and getattr(fileNode, 'parentNode', None):
            fileNode = fileNode.parentNode
        if hasattr(fileNode, 'title'):
            return getattr(fileNode.title, 'textContent', fileNode.title)
        return None
