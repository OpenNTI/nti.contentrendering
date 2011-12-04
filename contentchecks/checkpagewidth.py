import logging
logger = logging.getLogger( __name__ )

MAX_WIDTH = 730

def check(document, book):
	badPages = 0

	for pageid, page in book.pages.items():
		width = page.pageInfo['scrollWidth']

		if width > MAX_WIDTH:
			badPages += 1
			logger.warn( 'Width of %s (%s) is outside of bounds.  Maximum width should be %s but it was %s ',
						 page.filename, pageid, MAX_WIDTH, width )

	if badPages == 0:
		logger.info( 'All page sizes within acceptable range' )
