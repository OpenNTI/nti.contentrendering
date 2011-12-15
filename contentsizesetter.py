#!/usr/bin/env python2.7

import sys
import subprocess
from RenderedBook import RenderedBook

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

	eclipseTOC = book.toc
	for _, page in book.pages.items():
		storeContentSizes(page, eclipseTOC)

	eclipseTOC.save()

def storeContentSizes(page, eclipseTOC):

	contentHeight = page.scroll_height

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

if __name__ == '__main__':
	main(args)

