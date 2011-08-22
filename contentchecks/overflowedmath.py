import os

def check(document, book):
	javascript =  os.path.join(os.path.join(os.path.dirname(__file__), '../../js'), 'detectOverflowedMath.js')

	results = book.runPhantomOnPages(javascript)

	pagesWithBadMath = 0

	for node, maths in results.items():
		page = book.pages[node.getAttribute('ntiid')]
		if maths:
			pagesWithBadMath += 1
			print '*** WARNING *** Width of math elements %s is outside the bounds of %s.' % (maths, page.filename)

	if pagesWithBadMath == 0:
		print 'All math within page bounds'
