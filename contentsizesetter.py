#!/usr/bin/env python2.7

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
	_storeContentSizes( book.toc.root_topic )

	eclipseTOC.save()

def _storeContentSizes(topic):
	"""
	:param topic: An `IEclipseMiniDomTopic`.
	"""

	contentHeight = topic.scroll_height
	if contentHeight <= 0:
		logger.warn( "Failed to get content size for %s", topic )
		return

	topic.set_content_height( contentHeight )

	for child in topic.childTopics:
		_storeContentSizes( child )
