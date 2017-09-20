#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_property
from hamcrest import contains_string

import io
import os

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import ContentrenderingLayerTest
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString

preludes = (r'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',
            r'\usepackage{amsmath}')

patch_all()


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(preludes=preludes, bodies=maths)


class TestNTIHyperRef(ContentrenderingLayerTest):

    def test_ntiidref_basic(self):
        ref_str = r"""
        \ntiidref{SectionB}{NTI100}.
        """
        # Check that the DOM has the expected structure
        dom = _buildDomFromString(_simpleLatexDocument((ref_str,)))
        assert_that(dom.getElementsByTagName('ntiidref'), has_length(1))
        ref = dom.getElementsByTagName('ntiidref')[0]
        assert_that(ref, has_property('titleOverride', 'NTI100'))
        assert_that(ref,
                    has_property('attributes',
                                 has_entries('label', 'SectionB')))

    def test_ntiidref_links(self):
        source_str = r"""
        \chapter{A}
        \label{A}
        Some text
        \subsection{SubsectionA}
        \label{SubsectionA}
        This is in the same HTML page as the chapter.
        \chapter{B}
        \label{B}
        Some other text.
        \section{SectionB}
        \label{SectionB}
        Some text in subsection.
        """

        ref_str = r"""
        \chapter{One}
        \label{One}
        some text in chapter one
        
        \section{Two}
        Section refs \ntiidref{SectionB}{NTI100}
        """

        with RenderContext(_simpleLatexDocument((source_str,))) as source_context:
            source_context.render()
            with open(os.path.join(source_context.docdir, 'temp.paux'), 'rb') as f:
                paux_value = f.read()

        def load_links(document):
            paux_io = io.BytesIO(paux_value)
            document.context.restore(paux_io, rtype='XHTML')

        with RenderContext(simpleLatexDocumentText(preludes=preludes,
                                                   bodies=(ref_str,)),
                           packages_on_texinputs=True,
                           config_hook=load_links) as ref_context:
            ref_context.render()
            name = 'tag_nextthought_com_2011-10_testing-HTML-temp_Two.html'
            section_two = ref_context.read_rendered_file(name)

            assert_that(section_two,
                        contains_string('<a href="tag:nextthought.com,2011-10:testing-HTML-temp.SectionB">NTI100</a>'))
