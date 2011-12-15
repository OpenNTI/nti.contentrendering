#!/usr/bin/env python2.7

import sys
import subprocess
from RenderedBook import RenderedBook

import logging
logger = logging.getLogger(__name__)

contentSizeName = 'NTIRelativeScrollHeight'

def transform(book):
	"""
	Use the toc file to find all the pages in the contentLocation.
	Use phantomjs and js to render the page and extract the content size.
	Stuff the contentsize in the page as a meta tag and add it to toc
	"""

	eclipseTOC = book.toc
	for _, page in book.pages.items():
		storeContentSizes(page, eclipseTOC)

	eclipseTOC.save()

def storeContentSizes(page, eclipseTOC):

	contentHeight = page.scroll_height
	if contentHeight <= 0:
		logger.warn( "Failed to get content size for %s", page )
		return

	writeContentSizeToMeta(page.location, contentHeight)

	pageNode = eclipseTOC.getPageNodeWithNTIID(page.ntiid)

	pageNode.attributes[contentSizeName] = str(contentHeight)


def writeContentSizeToMeta(htmlFile, contentHeight):
	if htmlFile.startswith('./'):
		htmlFile = htmlFile[2:]

	# TODO: Convert to pyquery (once _Topic is merged with ContentPage and
	# the dom is persistent and shared)
	command = 'sed -i "" \
					  \"s/\\(<meta name=\\"NTIRelativeScrollHeight\\" content=\\"\\).*\\(\\" \\/>\\)/\\1%s\\2/\" %s' % (contentHeight, htmlFile)

	#print command

	subprocess.Popen(command, shell=True)

