from plasTeX.Renderers import Renderable as BaseRenderable
from plasTeX.Renderers import Renderer as BaseRenderer
from plasTeX.Renderers import mixin, unmix, baseclasses
from plasTeX.DOM import Node
from plasTeX.Logging import getLogger
from plasTeX.Filenames import Filenames
import os
log = getLogger()
import pdb

def createResourceRenderer(baserenderername):
	# Load renderer
	try:
		exec('from plasTeX.Renderers.%s import Renderer' % baserenderername)
	except ImportError, msg:
		log.error('Could not import renderer "%s".	Make sure that it is installed correctly, and can be imported by Python.' % baserenderername)
		raise

	#It would be nice to patch just the instance but PageTemplates render method calls BaseRenderer.render method
	BaseRenderer.render = renderDocument
	BaseRenderer.renderableClass = Renderable
	renderer = Renderer()


	return renderer

def renderDocument(self, document, postProcess=None):
	"""
	Invoke the rendering process

	This method invokes the rendering process as well as handling
	the setup and shutdown of image processing.

	Required Arguments:
	document -- the document object to render
	postProcess -- a function that will be called with the content of

	"""
	config = document.config

	# If there are no keys, print a warning.
	# This is most likely a problem.
	if not self.keys():
		log.warning('There are no keys in the renderer.	 ' +
					'All objects will use the default rendering method.')

	# Mix in required methods and members
	mixin(Node, type(self).renderableClass)
	Node.renderer = self

	# Create a filename generator
	self.newFilename = Filenames(config['files'].get('filename', raw=True),
								 (config['files']['bad-chars'],
								  config['files']['bad-chars-sub']),
								 {'jobname':document.userdata.get('jobname', '')}, self.fileExtension)

	self.cacheFilenames(document)



	# Invoke the rendering process
	if type(self).renderMethod:
		getattr(document, type(self).renderMethod)()
	else:
		unicode(document)


	# Run any cleanup activities
	self.cleanup(document, self.files.values(), postProcess=postProcess)

	# Write out auxilliary information
	pauxname = os.path.join(document.userdata.get('working-dir','.'),
							'%s.paux' % document.userdata.get('jobname',''))
	rname = config['general']['renderer']
	document.context.persist(pauxname, rname)

	# Remove mixins
	del Node.renderer
	unmix(Node, type(self).renderableClass)

class Renderable(BaseRenderable):


	@property
	def image(self):


		return self.getResource(['png', 'orig', 1])

	@property
	def vectorImage(self):
		return self.getResource(['svg'])


	def contents(self, criteria):
		return self.renderer.resourcedb.contentsAsString(self.getResource(criteria))

	def getResource(self, criteria):
		rs = self.getResourceSet()

		resource=None

		if rs:
			try:
				resources=rs.resources
				for crit in criteria:
					resources=resources[crit]

				resource=resources
			except KeyError:
				log.warning('resource for criteria %s does not exist for node %s'%(criteria, self))
				return None
		return resource


	def getResourceSet(self):
		return Node.renderer.resourcedb.getResourceSet(self)
