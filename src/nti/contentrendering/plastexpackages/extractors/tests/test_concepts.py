#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_entries
from hamcrest import assert_that

import os
import shutil
import tempfile

from nti.contentrendering.RenderedBook import RenderedBook

from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import ContentrenderingLayerTest

from nti.contentrendering.plastexpackages.extractors.concepts import _ConceptsExtractor

preludes = (
    '\\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',
)


class TestConceptsExtractor(ContentrenderingLayerTest):

  def data_file(self, fname):
    return os.path.join(os.path.dirname(__file__), 'data', fname)

  def setUp(self):
    super(TestConceptsExtractor, self).setUp()
    self.temp_dir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.temp_dir)

  def test_concepts_extractor_with_label(self):
    fname = 'sample_book_12.tex'
    with open(self.data_file(fname)) as fp:
      source_str = fp.read()

    with RenderContext(simpleLatexDocumentText(preludes=preludes,
                                               bodies=(source_str,))) as ref_context:
      ref_context.render()
      book = RenderedBook(ref_context.dom, ref_context.docdir)
      concept_extractor = _ConceptsExtractor()
      concept_index = concept_extractor.transform(book)
      hierarchy = concept_index['concepthierarchy']
      assert_that(hierarchy, has_entries("concepts",
                                         has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.concept:math",
                                                     has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1"],
                                                                 "name", "math")
                                                     )
                                         )
                  )

      concept_math = hierarchy["concepts"]['tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.concept:math']
      assert_that(concept_math, has_entries("concepts",
                                            has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.concept:algebra",
                                                        has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.section:1"],
                                                                    "name", "algebra"),
                                                        "tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.concept:subtraction",
                                                        has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.section:2"],
                                                                    "name", "subtraction")
                                                        )
                                            )
                  )

  def test_concepts_extractor_with_no_label(self):
    fname = 'sample_book_13.tex'
    with open(self.data_file(fname)) as fp:
      source_str = fp.read()

    with RenderContext(simpleLatexDocumentText(preludes=preludes,
                                               bodies=(source_str,))) as ref_context:
      ref_context.render()
      book = RenderedBook(ref_context.dom, ref_context.docdir)
      concept_extractor = _ConceptsExtractor()
      concept_index = concept_extractor.transform(book)
      hierarchy = concept_index['concepthierarchy']
      assert_that(hierarchy, has_entries("concepts",
                                         has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.math",
                                                     has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1"],
                                                                 "name", "math")
                                                     )
                                         )
                  )
      concept_math = hierarchy["concepts"]['tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.math']
      assert_that(concept_math, has_entries("concepts",
                                            has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.algebra",
                                                        has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.section:1"],
                                                                    "name", "algebra")
                                                        )
                                            )
                  )
      assert_that(concept_math, has_entries("concepts",
                                            has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.subtraction",
                                                        has_entries("contentunitntiids", ["tag:nextthought.com,2011-10:testing-HTML-temp.section:2"],
                                                                    "name", "subtraction")
                                                        )
                                            )
                  )

  def test_concepts_extractor_with_multiple_chapter_refs(self):
    fname = 'sample_book_14.tex'
    with open(self.data_file(fname)) as fp:
      source_str = fp.read()

    with RenderContext(simpleLatexDocumentText(preludes=preludes,
                                               bodies=(source_str,))) as ref_context:
      ref_context.render()
      book = RenderedBook(ref_context.dom, ref_context.docdir)
      concept_extractor = _ConceptsExtractor()
      concept_index = concept_extractor.transform(book)
      hierarchy = concept_index['concepthierarchy']
      assert_that(hierarchy, has_entries("concepts",
                                         has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.math",
                                                     has_entries("contentunitntiids", [u'tag:nextthought.com,2011-10:testing-HTML-temp.chapter_2'],
                                                                 "name", "math")
                                                     )
                                         )
                  )

      assert_that(hierarchy, has_entries("concepts",
                                         has_entries("tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.nfpa_1720",
                                                     has_entries("contentunitntiids", [u'tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1', u'tag:nextthought.com,2011-10:testing-HTML-temp.chapter_2'],
                                                                 "name", "NFPA 1720")
                                                     )
                                         )
                  )
