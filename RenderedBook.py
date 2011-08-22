from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
import pdb


def _runPhantomOnPage(contentLocation, tocNode, scriptName):
	htmlFile = os.path.join(contentLocation, tocNode.getAttribute('href'))
	#print 'Fetching page info for %s' % htmlFile
	process = "phantomjs %s %s 2>/dev/null" % (scriptName, htmlFile)
	#print process
	jsonStr = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
	#print '%s-%s' % (htmlFile, jsonStr)
	result = json.loads(jsonStr)
	return (tocNode, result)


class RenderedBook(object):
	TOC_FILE_NAME = 'eclipse-toc.xml'

	document = None
	contentLocation = None
	tocFile = None

	pages = {} #id to ContentPage

	def __init__(self, document, location):
		self.contentLocation = location
		self.tocFile = os.path.join(self.contentLocation, self.TOC_FILE_NAME)
		self.document = document
		self._processPages()

		for pageid, page in self.pages.items():
			print '%s -> %s' % (pageid, page.ntiid)


	def _processPages(self):
		javascript =  os.path.join(os.path.join(os.path.dirname(__file__), '../js'), 'getPageInfo.js')

		results = self.runPhantomOnPages(javascript)

		for node, pageinfo in results.items():
			page = ContentPage(os.path.join(self.contentLocation, node.getAttribute('href')), pageinfo, node)
			self.pages[page.ntiid] = page



	def getEclipseTOC(self):
		return EclipseTOC(self.tocFile)

	def runPhantomOnPages(self, script):
		eclipseTOC = EclipseTOC(self.tocFile)
		nodesForPages = eclipseTOC.getPageNodes()

		results = {}

		with ProcessPoolExecutor() as executor:
			for the_tuple in executor.map( _runPhantomOnPage, [self.contentLocation for x in nodesForPages if x], \
										   nodesForPages, [script for x in nodesForPages if x]):
				node = the_tuple[0]
				result = the_tuple[1]

				results[node] = result

		return results




class EclipseTOC(object):
	file = None
	dom = None

	def __init__(self, f):
		self.file = f
		self.dom = parse(self.file)

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
		f = open(self.file, 'w')
		self.dom.writexml(f)
		f.close()


class ContentPage(object):

	def __init__(self, location, pageInfo, tocNode):
		self.pageInfo = pageInfo
		self.filename = tocNode.getAttribute('href')
		self.ntiid = pageInfo['ntiid']
		self.title = tocNode.getAttribute('label')
		self.location = location

