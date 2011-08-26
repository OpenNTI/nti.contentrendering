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

	eclipseTOC = book.getEclipseTOC()
	for pageid, page in book.pages.items():
		storeContentSizes(page, eclipseTOC)

	eclipseTOC.save()

def storeContentSizes(page, eclipseTOC):

	contentHeight = page.pageInfo['scrollHeight']

	writeContentSizeToMeta(page.location, contentHeight)

	pageNode = eclipseTOC.getPageNodeWithNTIID(page.ntiid)

	pageNode.attributes[contentSizeName] = str(contentHeight)


def writeContentSizeToMeta(htmlFile, contentHeight):
	if htmlFile.startswith('./'):
		htmlFile = htmlFile[2:]

	command = 'sed -i .bkp \
					  \"s/\\(<meta name=\\"NTIRelativeScrollHeight\\" content=\\"\\).*\\(\\" \\/>\\)/\\1%s\\2/\" %s' % (contentHeight, htmlFile)

	#print command

	subprocess.Popen(command, shell=True)

	backupFile = htmlFile+'.bkp'

	if os.path.exists(backupFile):
		os.remove(backupFile)

if __name__ == '__main__':
	main(args)

