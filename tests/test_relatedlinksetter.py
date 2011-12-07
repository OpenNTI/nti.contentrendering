from . import ConfiguringTestBase
from nti.contentrendering.relatedlinksetter import performTransforms
from nti.contentrendering.RenderedBook import RenderedBook

import os
from hamcrest import assert_that, has_length, greater_than_or_equal_to, is_

class EmptyMockDocument(object):

	childNodes = ()

	def __init__(self):
		self.context = {}

	def getElementsByTagName(self, name): return ()

def _phantom_function( htmlFile, scriptName, args, key ):
	return (key, {'ntiid': key[0]})

class NoPhantomRenderedBook(RenderedBook):

	def _get_phantom_function(self):
		return _phantom_function



class TestTransforms(ConfiguringTestBase):

	def test_transforms(self):
		book = NoPhantomRenderedBook( EmptyMockDocument(), os.path.join( os.path.dirname( __file__ ),  'intro-biology-rendered-book' ) )
		res = performTransforms( book, save_toc=False )
		assert_that( res, has_length( greater_than_or_equal_to( 3 ) ) )
		assert_that( book.toc.dom.getElementsByTagName( "video" ), has_length( 1 ) )
		assert_that( book.toc.dom.getElementsByTagName( "video" )[0].parentNode.parentNode.getAttribute( "ntiid" ),
					 is_("tag:nextthought.com,2011-10:ck12-HTML-book-tx.1") )
