from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os

def pageForTOCEntry(node):
	if getattr(node, 'hasAttributes', None) and node.hasAttribute('href'):
		return getPage(os.path.basename(node.getAttribute('href')))
	return None
import pdb
def pages(tocDOM):
   	files = findFilesForNode(tocDOM.getElementsByTagName('toc')[0])
   	return [os.path.basename(f) for f in files]

def findFilesForNode(node):
	files = []
	if node.hasAttribute('href'):
		files.append(node.getAttribute('href'))

	for topic in node.getElementsByTagName('topic'):
		if topic.hasAttribute('href'):
			files.append(topic.getAttribute('href'))

	return files

javascript =  os.path.join(os.path.join(os.path.dirname(__file__), '../js'), 'getPageInfo.js')
def _getPageInfo(htmlFile):
	#print 'Fetching page info for %s' % htmlFile
	process = "phantomjs %s %s 2>/dev/null" % (javascript, htmlFile)
	#print process
	jsonStr = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
	pageInfo = json.loads(jsonStr)
	return (htmlFile, pageInfo)

class RenderedBook(object):
	TOC_FILE_NAME = 'eclipse-toc.xml'

	contentLocation = None
	tocFile = None
	pages = {}

	def __init__(self, location):
		self.contentLocation = location
		self.tocFile = os.path.join(self.contentLocation, self.TOC_FILE_NAME)

		self._processPages()


	def _processPages(self):
		fullPathForFiles = [os.path.join(self.contentLocation, f) for f in pages(self.getTOC())]

		with ProcessPoolExecutor() as executor:
			for the_tuple in executor.map( _getPageInfo, fullPathForFiles):
				self.pages[os.path.basename(the_tuple[0])]=ContentPage(the_tuple[0], the_tuple[1])

	def getTOC(self):
		return parse(self.tocFile)

	def persistTOC(self, tocDOM, location=None):
		if location is None:
			location = self.tocFile

		f = open(location, 'w')
		tocDOM.writexml(f)
		f.close()

	def pageForTOCNode(self, node):
		if getattr(node, 'hasAttributes', None) and node.hasAttribute('href'):
			return self.getPage(node.getAttribute('href'))

		return None

	def getContentInfo(self):
		if not hasattr(self, '_contentinfo', None):
			self._contentinfo = ContentInfo(self.getTOC())

		return self._contentinfo


	def getPage(self, pageName):
		return self.pages[pageName]

	def getPageNames(self):
		return self.pages.keys()



class ContentPage(object):

	def __init__(self, location, pageInfo):
		self.location = location #Full path to content file
		self.name = os.path.basename(self.location)
		self.pageInfo = pageInfo
