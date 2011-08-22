
MAX_WIDTH = 730

def check(document, book):
	badPages = 0

	for pageid, page in book.pages.items():
		width = page.pageInfo['scrollWidth']

		if width > MAX_WIDTH:
			badPages += 1
			print '*** WARNING *** Width of %s is outside of bounds.  Maximum width should be %s but it was %s ' % (page.filename, MAX_WIDTH, width)

	if badPages == 0:
		print 'All page sizes within acceptable range'
