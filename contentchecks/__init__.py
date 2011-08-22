import pdb, os, sys, glob
from plasTeX.Logging import getLogger

log = getLogger()

def performChecks(document, book):
	checksDir = os.path.dirname(__file__)

	modules = [os.path.splitext(os.path.basename(fileName))[0] for fileName in \
			   glob.glob(os.path.join(checksDir, '*.py')) \
			   if not '__init__' in fileName]

	for moduleName in modules:
		module = 'contentchecks.%s' % moduleName
		try:
			exec('from %s import check as check' % module)
		except ImportError, msg:
			log.error('Could not import check from "%s".  Make sure that it is installed correctly, and can be imported by Python.' % module)
			continue

		print 'Running check for %s' % module
		check(document, book)
