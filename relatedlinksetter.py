#!/usr/bin/env python
import sys
from RenderedBook import RenderedBook
import pdb
import itertools

def main(args):
 	""" Main program routine """

	if not len(args)>0:
		print "Usage: contentsizesetter.py path/to/content"
		sys.exit()

	contentLocation = args.pop(0)

	transform(RenderedBook(contentLocation))

def transform(book):
	"""
	Use the toc file to find all the pages in the contentLocation.
	Use phantomjs and js to render the page and extract the content size.
	Stuff the contentsize in the page as a meta tag and add it to toc
	"""

	eclipseTOC = book.getEclipseTOC()

	addRelatedBasedOnLinks(eclipseTOC, book)
	addRelatedBasedOnTOC(eclipseTOC, book)

	eclipseTOC.save()



from collections import defaultdict
def addRelatedBasedOnTOC(eclipseTOC, book):
	relatedTuples = []

	theIndex = book.document.getElementsByTagName('printindex')[0]

	for group in theIndex.groups:
		entries = [ entry for column in group for entry in column]

		for entry in entries:
			related = relatedPagesForIndexEntry(book, eclipseTOC, entry)
			relatedTuples.append(related)

	relatedTuples = [t for t in relatedTuples if len(t[1])>0]

	for key, relationships in relatedTuples:
		for relatesTo, relatedTo in relationships:
			markRelated(eclipseTOC, relatesTo, relatedTo, 'index', qualifier=key)


def relatedPagesForIndexEntry(book, eclipseTOC, entry):
	related = []
	pages = [book.pages[eclipseTOC.getPageForDocumentNode(page).getAttribute('ntiid')] for page in entry.pages]
	pageIds = [page.ntiid for page in pages if page is not None]

	related.extend( [x for x in itertools.permutations(pageIds, 2) if x[0]!=x[1]] )

	for childEntry in entry.childNodes:
		childRelated = relatedPagesForIndexEntry(book, eclipseTOC,  childEntry)
		related.extend(childRelated[1])

	return (entry.key.textContent, related)

def addRelatedBasedOnLinks(eclipseTOC, book):
	for id, page in book.pages.items():
		addOutgoingLinks(eclipseTOC, page)

import re
filere = re.compile('(?P<file>.*?\.html).*')
def stripToFile(link):
	file = None

	match = filere.match(link)
	if match:
		file = match.group('file')

	return file

def addOutgoingLinks(eclipseTOC, page):


	fileNameAndLinkList = [(stripToFile(link), link) for link in page.pageInfo['OutgoingLinks']]

	for fileNameAndLink in fileNameAndLinkList:
		fileName = fileNameAndLink[0]
		link = fileNameAndLink[1]

		tocNode = eclipseTOC.getPageNodeWithAttribute('href', fileName)[0]

		if fileName and link:
			markRelated(eclipseTOC, page.ntiid, tocNode.getAttribute('ntiid'), 'link', qualifier=link)


def markRelated(eclipseTOC, relatesTo, relatedTo, reason, qualifier=""):
	relatesToNode =  eclipseTOC.getPageNodeWithNTIID(relatesTo)
	markNodesRelated(eclipseTOC, relatesToNode, relatedTo, reason, qualifier)

def markNodesRelated(eclipseTOC, relatesToNode, relatedToIds, reason, qualifier=""):
	relatedPages = getOrCreateNode(eclipseTOC.dom, relatesToNode, 'Related')

	if not isinstance(relatedToIds, list):
		relatedToIds = [relatedToIds]

	alreadyrelatednodes = [node for node in relatedPages.childNodes]

	for idToAdd in relatedToIds:
		if all([not pageIs(node, idToAdd, reason, qualifier) for node in alreadyrelatednodes]):
			relatedPages.appendChild(createTOCPageNode(eclipseTOC.dom, idToAdd, reason, qualifier))

def pageIs(page1, ntiid, type, qualifier):

	if not nodeHasAttrval(page1, 'ntiid', ntiid):
		return False

	if not nodeHasAttrval(page1, 'type', type):
		return False

	if not nodeHasAttrval(page1, 'qualifier', qualifier):
		return False

	return True

def nodeHasAttrval(node1, attrname, attrval):
	if not node1.hasAttribute(attrname):
		return False

	return node1.getAttribute(attrname) == attrval

def createTOCPageNode( document, ntiid, type, qualifier=""):
	pageNode = document.createElement('page')

	pageNode.setAttribute('ntiid', ntiid)
	pageNode.setAttribute('type', type)
	pageNode.setAttribute('qualifier', qualifier)

	return pageNode

def getOrCreateNode(document, parent, nodeName):
	node = parent.getElementsByTagName(nodeName)

	if len(node) > 0:
		node = node[0]
	else:
		node = document.createElement(nodeName)
		parent.appendChild(node)

	return node

if __name__ == '__main__':
	main(args)

