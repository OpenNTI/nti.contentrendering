
import pdb, os, sys, glob
from plasTeX.Logging import getLogger

log = getLogger()

def performTransforms(document):
	transformsDir = os.path.dirname(__file__)

	modules = [os.path.splitext(os.path.basename(fileName))[0] for fileName in \
			   glob.glob(os.path.join(transformsDir, '*.py')) \
			   if not '__init__' in fileName]

	for moduleName in modules:
		module = 'transforms.%s' % moduleName
		try:
			exec('from %s import transform as transform' % module)
		except ImportError, msg:
			log.error('Could not import transforms from "%s".  Make sure that it is installed correctly, and can be imported by Python.' % module)
			continue

		print 'Running transform for %s' % module
		transform(document)
