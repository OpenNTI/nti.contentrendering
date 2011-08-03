#!/usr/bin/env python


import os
import re
import sys
from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from RenderedBook import RenderedBook

javascript = os.path.join('%s'%(os.path.dirname(__file__)),'getContentSize.js')

contentSizeName = 'NTIRelativeScrollHeight'

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

	storeContentSizes(book,tocDOM.getElementsByTagName('toc')[0])

	book.persistTOC(tocDOM)

def storeContentSizes(book, node):

	page = book.pageForTOCNode(node)

	if page is None:
 		print 'Unknown page for node %s' % node
		return

	contentHeight = page.pageInfo['scrollHeight']

	writeContentSizeToMeta(page.location, contentHeight)
	node.attributes[contentSizeName]=str(contentHeight)

	for child in node.childNodes:
		if getattr(child, 'hasAttributes', None) and child.hasAttribute('href'):
			storeContentSizes(book, child);


def writeContentSizeToMeta(htmlFile, contentHeight):
	if htmlFile.startswith('./'):
		htmlFile = htmlFile[2:]

	command = 'sed -i .bkp \
					  \"s/\\(<meta name=\\"NTIRelativeScrollHeight\\" content=\\"\\).*\\(\\" \\/>\\)/\\1%s\\2/\" %s' % (contentHeight, htmlFile)

	#print command

	subprocess.Popen(command, shell=True)

	backupFile = htmlFile+'.bkp'

	if os.path.exists(backupFile):
		os.remove(htmlFile+'.bkp')

if __name__ == '__main__':
	main(args)

