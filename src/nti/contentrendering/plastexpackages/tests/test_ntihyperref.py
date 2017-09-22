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
        \section{SectionB}
        \label{SectionB}
        Some text in subsection.
        \subsection{SubsectionB}
        \label{SubsectionB}
        \section{SectionC}
        This is in the same HTML page as the section.
        \ntiidref{SectionB}<NTI100>.
        \ntiidref{SubsectionB}.
        """
        # Check that the DOM has the expected structure
        dom = _buildDomFromString(_simpleLatexDocument((ref_str,)))
        refs = dom.getElementsByTagName('ntiidref')
        assert_that(refs, has_length(2))
        assert_that(refs[0].attributes, has_entries('title', 'NTI100'))
        assert_that(refs[0].idref['label'].title, has_property('source', 'SectionB'))
        assert_that(refs[0],
                    has_property('attributes',
                                 has_entries('label', 'SectionB')))
        assert_that(refs[1].attributes, has_entries('title', None))
        assert_that(refs[1].idref['label'].title, has_property('source', 'SubsectionB'))
        assert_that(refs[1],
                    has_property('attributes',
                                 has_entries('label', 'SubsectionB')))

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
        \subsection{SubsectionB}
        \label{SubsectionB}
        This is in the same HTML page as the section.
        """

        ref_str = r"""
        \chapter{One}
        \label{One}
        some text in chapter one
        
        \section{Two}
        Section refs \ntiidref{SectionB}<NTI100>
        Section refs \ntiidref{SubsectionB}
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

            assert_that(section_two,
                        contains_string('<a href="tag:nextthought.com,2011-10:testing-HTML-temp.SectionB#SubsectionB">SubsectionB</a>'))
