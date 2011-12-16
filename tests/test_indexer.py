import unittest

from nti.contentrendering.indexer import get_microdata
from hamcrest import assert_that, has_length, is_

class TestIndexer(unittest.TestCase):

	def _has_tuple(self, results, index, t):
		assert_that(results[index], is_(t))
		
	def test_get_microdata(self):
		raw = """
			<html>
			<a name="one" itemscope itemtype="http://schema.org/CreativeWork">what a fuck is going on
			<span itemprop="fraction">.</span>
			<span itemprop="multiplication"/>
			<div><h1>to enter</h1></div>
			<img name="two" itemscope itemtype="http://schema.org/CreativeWork" />
			<a name="three" itemscope itemtype="http://schema.org/CreativeWork" >
			<span itemprop="prime">.</span>
			<span itemprop="trinity"/>
			</a>
			</a>
			<a name="four" itemscope itemtype="http://schema.org/CreativeWork" >
			<span itemprop="divisible">.</span>
			<span itemprop="pair"/>
			</a>
			</html>
			"""
		ls = get_microdata(raw)
		assert_that(ls, has_length(4))
		self._has_tuple(ls, 0, (u'one', [u'fraction', u'multiplication']))
		self._has_tuple(ls, 1, (u'four', [u'divisible', u'pair']))
		self._has_tuple(ls, 2, (u'two', []))
		self._has_tuple(ls, 3, (u'three', [u'prime', u'trinity']))
		
if __name__ == '__main__':
	unittest.main()
	