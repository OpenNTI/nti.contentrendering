#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904


from hamcrest import assert_that
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import has_entry

from nti.contentrendering.tests import ContentrenderingLayerTest

from nti.contentrendering.tests import buildDomFromString as _buildDomFromString
from nti.contentrendering.tests import simpleLatexDocumentText

from nti.contentrendering.transforms.trans_caption import transform as captionTransform

def _simpleLatexDocument(maths):
	return simpleLatexDocumentText( preludes=(br'\usepackage{nti.contentrendering.plastexpackages.graphicx}',
						  br'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}'),
					bodies=maths )

class TestCaptionTransform(ContentrenderingLayerTest):

	def test_captionTransform(self):
		example = br"""
	\begin{figure*}
	\includegraphics{sample}
	\caption*{Caption 1}
	\end{figure*}

	\begin{figure*}
	\ntiincludeannotationgraphics{sample}
	\caption*{Caption 2}
	\end{figure*}

	\begin{figure*}
	\ntiincludenoannotationgraphics{sample}
	\caption*{Caption 3}
	\end{figure*}

	\begin{table}
	\begin{tabular}{ll}
	& \\
	\end{tabular}
	\caption*{Caption4}
	\end{table}
		"""

		dom = _buildDomFromString( _simpleLatexDocument( (example,) ) )

		captions = dom.getElementsByTagName('caption')
		assert_that( captions, has_length(4))

		#run the transform
		captionTransform( dom )

		assert_that( captions[0].style, has_entry( 'display', 'none' ) )
		assert_that( captions[1].style, has_entry( 'display', 'none' ) )
		assert_that( captions[2].style, has_entry( 'display', 'none' ) )
		assert_that( captions[3].style, is_not(has_entry( 'display', 'none' )) )
