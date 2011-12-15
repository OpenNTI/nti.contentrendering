
from xml.dom.minidom import parse
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
import warnings

from zope.deprecation import deprecate
from zope import interface
from . import interfaces
from . import minidom_writexml

import logging
logger = logging.getLogger( __name__ )

warnings.warn( "Using whatever phantomjs is on the path" )
def _runPhantomOnPage( htmlFile, scriptName, args, key ):
	process = "phantomjs %s %s %s 2>/dev/null" % (scriptName, htmlFile, " ".join([str(x) for x in args]))
	jsonStr = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
	try:
		result = json.loads(jsonStr)
	except:
		logger.exception( "Failed to read json (%s) from %s", jsonStr, process )
		raise
	return (key, result)


class RenderedBook(object):

	interface.implements(interfaces.IRenderedBook)

	TOC_FILE_NAME = 'eclipse-toc.xml'

	document = None
	contentLocation = None
	tocFile = None

	def __init__(self, document, location):
		self.contentLocation = location
		self.tocFile = os.path.join(self.contentLocation, self.TOC_FILE_NAME)
		self.document = document
		self.pages = {}
		self._toc = None
		self._processPages()

		for pageid, page in self.pages.items():
			logger.debug( '%s -> %s', pageid, page.ntiid )
		logger.info( "Book at %s had %d pages", os.path.abspath(location), len(self.pages) )


	def _processPages(self):
		javascript =  os.path.join( os.path.dirname(__file__), 'js', 'getPageInfo.js')
		if not os.path.exists( javascript ): raise Exception( "Unable to get page info script %s" % javascript )

		results = self.runPhantomOnPages(javascript)

		for (_,href,label), pageinfo in results.items():
			page = ContentPage( os.path.join(self.contentLocation, href), pageinfo, href, label )
			self.pages[page.ntiid] = page

	@property
	def jobname(self):
		try:
			return self.document.userdata.get('jobname', '')
		except AttributeError:
			return ''

	@property
	def toc(self):
		"""
		An :class:`EclipseTOC` object. Changes made to the returned
		object are persistent in memory for the life of this object (and possibly on disk).
		"""
		if self._toc is None:
			self._toc = EclipseTOC(self.tocFile)
		return self._toc

	@deprecate("Prefer the toc property")
	def getEclipseTOC(self):
		"""
		Returns a newly parsed TOC object.
		"""
		return EclipseTOC(self.tocFile)

	def _get_phantom_function(self):
		"""
		This cannot be simply a class attribute because
		it gets wrapped as an instance method automatically.
		:return: The pickalable function to map across nodes.
		"""
		return _runPhantomOnPage

	def runPhantomOnPages(self, script, *args):
		"""
		:return: Dictionary of {(ntiid,href,label) => object from script}
		"""

		eclipseTOC = self.toc
		nodesForPages = eclipseTOC.getPageNodes()

		# Notice that we very carefully do not send anything attached
		# to the DOM itself over to the executor processess. Not only
		# is it large to serialize, it is potentially
		# risky: arbitrary, non-pickalable objects could get attached there
		results = {}

		with ProcessPoolExecutor() as executor:
			for the_tuple in executor.map( self._get_phantom_function(),
										   [os.path.join( self.contentLocation, node.getAttribute( 'href' ) )
											for node in nodesForPages],
										   [script] * len(nodesForPages),
										   [args] * len(nodesForPages),
										   [(node.getAttribute('ntiid'),node.getAttribute('href'),node.getAttribute('label'))
											 for node in nodesForPages]):
				key = the_tuple[0]
				result = the_tuple[1]

				results[key] = result

		return results

class EclipseTOC(object):
	interface.implements(interfaces.IEclipseMiniDomTOC)

	def __init__(self, f):
		self.filename = f
		self.dom = parse(self.filename)
		# We may or may not have an href for the root toc yet.
		# If not, assume it to be index.html
		tocs = self.dom.getElementsByTagName( "toc" )
		if len(tocs) == 1 and not tocs[0].getAttribute( "href" ):
			tocs[0].setAttribute( "href", "index.html" )

	@property
	@deprecate("Prefer the `filename` property.")
	def file(self):
		return self.filename

	# FIXME These names need adjustment. There are "page" XML nodes, but the method
	# names below use "page" to mean a page in the the TOC, i.e., a 'topic' or 'toc'
	# node

	def getPageForDocumentNode(self, node):
		#Walk up the node try untill we find something with an id that matches our label
		if node is None:
			return None

		title = None
		if getattr(node, 'title', None):
			title = node.title.textContent if hasattr(node.title, 'textContent') else node.title
		matchedNodes = []
		if title:
			matchedNodes = self.getPageNodeWithAttribute('label', title)

		if len(matchedNodes) > 0:
			return matchedNodes[0]


		return self.getPageForDocumentNode(node.parentNode)

	def getPageNodeWithNTIID(self, ntiid, node=None):
		return self.getPageNodeWithAttribute('ntiid', value = ntiid, node = node)[0]

	def getPageNodeWithAttribute(self, name, value=None, node=None):

		if node is None:
			node = self.getRootTOCNode()

		nodes = []
		if (node.nodeName == 'topic' or node.nodeName == 'toc') and \
			   getattr(node, 'hasAttribute', None) and node.hasAttribute(name):
			if value is None or node.getAttribute(name) == value:
				nodes.append(node)

		for child in node.childNodes:
			nodes.extend(self.getPageNodeWithAttribute(name, value=value, node=child))

		return nodes

	def getRootTOCNode(self):
		return self.dom.getElementsByTagName('toc')[0]

	def getPageNodes(self):
		return [x for x in self.getPageNodeWithAttribute('href', node=None) if x.hasAttribute('ntiid')]

	def save(self):
		minidom_writexml( self.dom, self.filename )


class ContentPage(object):

	def __init__(self, location, pageInfo, href, label):
		self._pageInfo = pageInfo
		self.filename = href
		self.ntiid = pageInfo['ntiid']
		self.title = label
		self.location = location

	@property
	@deprecate("Prefer to access the specific property")
	def pageInfo(self):
		return self._pageInfo

	@property
	def outgoing_links(self):
		"A sequence of strings naming links from this page."
		return self._pageInfo.get('OutgoingLinks',())

	@property
	def scroll_height(self):
		"""
		:return: An integer giving the relative height of the content of this page.
		:raises KeyError: If no size is known.
		"""
		return self._pageInfo['scrollHeight']

	@property
	def scroll_width(self):
		"""
		:return: An integer giving the relative width of the content of this page.
		:raises KeyError: If no size is known
		"""
		return self._pageInfo['scrollWidth']

	def get_scroll_width( self, default=-1 ):
		"""
		:return: The scroll width if known, otherwise the `default` (-1)
		"""
		return self._pageInfo.get( 'scrollWidth', default )

