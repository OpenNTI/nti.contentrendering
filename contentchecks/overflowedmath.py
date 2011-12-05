import os
import logging
logger = logging.getLogger(__name__)

import nti.contentrendering

def check(document, book):
	javascript =  os.path.join( os.path.dirname( nti.contentrendering.__file__), 'js', 'detectOverflowedMath.js' )
	if not os.path.exists( javascript ): raise Exception( "Unable to get %s" % javascript )

	results = book.runPhantomOnPages(javascript)

	pagesWithBadMath = 0

	for node, maths in results.items():
		page = book.pages[node.getAttribute('ntiid')]
		if maths:
			pagesWithBadMath += 1
			logger.warn( 'Width of math elements %s is outside the bounds of %s.', maths, page.filename )

	if pagesWithBadMath == 0:
		logger.info( 'All math within page bounds' )
