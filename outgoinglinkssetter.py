#!/usr/bin/env python

from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from RenderedBook import RenderedBook


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

	tocDOM = book.getTOC()

	nodes = [tocDOM.getElementsByTagName('toc')[0]]
	nodes.extend(tocDOM.getElementsByTagName('topic'))

	for node in nodes:
		page = book.pageForTOCNode(node)

		if page is None:
			print 'Unknown page for node %s' % node
			continue

		addOutgoingLinks(book, page, tocDOM, node)

	book.persistTOC(tocDOM)

def addOutgoingLinks(book, page, tocDOM, node):

	linksNode = tocDOM.createElement('outgoinglinks')

	#print 'Writing links for page %s' % page.location

	for link in page.pageInfo['OutgoingLinks']:

		linkNode = tocDOM.createElement('page')

		destpage = book.getPage(link)

		if destpage:
			linkNode.setAttribute('NTIID', destpage.pageInfo['NTIID'])

		linkNode.appendChild(tocDOM.createTextNode(destpage.name))
		linksNode.appendChild(linkNode)

	node.appendChild(linksNode)

if __name__ == '__main__':
	main(args)

