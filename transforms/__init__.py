import os
import glob

from plasTeX.Logging import getLogger

logger = getLogger(__name__)

def performTransforms(document):
	transformsDir = os.path.dirname(__file__)

	modules = [os.path.splitext(os.path.basename(fileName))[0]
				for fileName in glob.glob(os.path.join(transformsDir, '*.py'))
				if not '__init__' in fileName]

	for moduleName in modules:
		_name = 'transforms.%s' % moduleName
		try:
			_name = 'transforms.%s' % moduleName
			_module = __import__(_name, globals(), locals(), ['transform'], -1)
		except ImportError:
			logger.error('Could not import transforms from "%s".' % _name)
			continue

		logger.info( 'Running transform for %s', _name )

		_module.transform(document)
