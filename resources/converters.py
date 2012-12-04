#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base classes and useful functionality for implementing :class:`interfaces.IContentUnitRepresentationBatchConverter`
objects.

$Id$
"""
from __future__ import print_function, unicode_literals

import os
import re
import subprocess
import time
from StringIO import StringIO
import codecs
import shutil
import tempfile

from zope import interface

from plasTeX.Imagers import WorkingFile
from plasTeX.Filenames import Filenames

from nti.contentrendering import ConcurrentExecutor as ProcessPoolExecutor

from . import interfaces

_marker = object()
logger = __import__('logging').getLogger(__name__)

@interface.implementer(interfaces.IContentUnitRepresentationBatchConverter)
class AbstractContentUnitRepresentationBatchConverter(object):
	"""
	Implements batch conversion of resources by acting as a wrapper
	to drive an object that can compile and transform a batch of resources at once.
	"""

	_final_methods = ('storeKeys','createResourceSetGenerator',
					   'generateResources', 'storeResources', 'canGenerate',
					   '_prepare_compile_driver_with_sources')


	def __init__(self, document):
		self.document = document
		self.batch_args = ()
		self.batch_kwargs = {}
		for final in self._final_methods:
			if getattr( self, final ) is not getattr( AbstractContentUnitRepresentationBatchConverter, final ):
				raise ValueError( "Cannot override deprecated method %s" % final ) #pragma: no cover


	def _new_batch_converter_driver(self, *args, **kwargs):
		"""
		Returns an object with a `convert_batch(generatable_content_units)` method used to handle
		a batch conversion. (See :func:`AbstractCompilingContentUnitRepresentationBatchConverter.convert_batch`).

		This class will pass the values of `self.batch_args` and `self.batch_kwargs` to this
		method.
		"""
		raise NotImplementedError # pragma: no cover

	def _can_process( self, content_unit ):
		return True

	def process_batch( self, content_units ):

		generatable_units = [s for s in content_units if self._can_process( s )]
		if len(generatable_units) != len(content_units):
			logger.warn( "Given sources that cannot be generated by this object" )

		size = len(generatable_units)
		if not size > 0:
			return ()

		return self._new_batch_converter_driver( *self.batch_args, **self.batch_kwargs ).convert_batch( generatable_units )



@interface.implementer(interfaces.IContentUnitRepresentationBatchCompilingConverter)
class AbstractCompilingContentUnitRepresentationBatchConverter(AbstractContentUnitRepresentationBatchConverter):
	"""
	Implements batch conversion of resources by acting as a wrapper
	to drive an object (a :class:`AbstractDocumentCompilerDriver`) that can compile and
	transform a batch of resources at once.
	"""

	compiler = ''
	debug = False

	def _new_batch_converter_driver(self, *args, **kwargs ):
		return self

	def _new_batch_compile_driver( self, document, *args, **kwargs ):
		raise NotImplementedError  # pragma: no cover

	def _prepare_compile_driver_with_content_units( self, content_units ):
		encoding = self.document.config['files']['input-encoding']
		generator = self._new_batch_compile_driver( self.document, compiler=self.compiler, encoding=encoding)
		generator.writePreamble()
		for unit in content_units:
			generator.add_content_unit_to_batch(unit)
		generator.writePostamble()
		return generator


	def convert_batch( self, content_units ):
		"""
		:param content_units: The units of content (e.g., plasTeX DOM Node objects)
			that we are to convert. We assume that it has already been established
			that they can be converted.
		"""
		generator = self._prepare_compile_driver_with_content_units( content_units )

		return generator.compile_batch_to_representations()

class AbstractConcurrentCompilingContentUnitRepresentationBatchConverter(AbstractCompilingContentUnitRepresentationBatchConverter):
	"""
	Exists to add concurrency support to a compilation process.
	"""
	concurrency = 1


	def convert_batch( self, content_units ):
		if self.concurrency == 1 or len(content_units) == 1:
			return super(AbstractConcurrentCompilingContentUnitRepresentationBatchConverter,self).convert_batch( content_units )

		chunks = [[] for _ in range(self.concurrency)]
		for i, unit in enumerate(content_units):
			chunks[i % self.concurrency].append( unit )

		generators = [self._prepare_compile_driver_with_content_units( chunk ) for chunk in chunks]
		results = []
		params = [True] * self.concurrency

		with ProcessPoolExecutor() as executor:
			for resources in executor.map(_processBatchSource, generators, params):
				results.extend( resources )

		return results


class AbstractConcurrentConditionalCompilingContentUnitRepresentationBatchConverter(AbstractConcurrentCompilingContentUnitRepresentationBatchConverter):
	"""
	Extends the generic concurrent compilation process by implementing the :meth:`_can_process`
	method. By default, checks the contents of `illegalCommands` as a sequence of regular expressions
	against each source; if it matches, it cannot be processed.
	"""

	illegalCommands	= ()

	def _can_process(self, content_unit):
		if not self.illegalCommands:
			return True

		source = content_unit.source
		for command in self.illegalCommands:
			if re.search(command, source):
				return False
		return True


def _processBatchSource(generator, params, raise_exceptions=False):
	"""
	:param bool raise_exceptions: When called an a concurrent.futures pool,
		then exceptions from the job method (this method) can cause the pool
		to hang. If ``False`` (the default), then this method will swallow
		exceptions.
	"""
	try:
		if generator.size() > 0:
			return generator.compile_batch_to_representations()
	except Exception:
		# Running in a concurrent.futures, throwing tends to
		# hang the pool.
		# NOTE that the pool we usually use now does not have that problem.
		# however, we want to customize the return value so as not to cause
		# further problems.
		if raise_exceptions:
			raise
		import traceback; traceback.print_exc()

	return ()

for _x in AbstractContentUnitRepresentationBatchConverter._final_methods:
	setattr( AbstractContentUnitRepresentationBatchConverter, _x, _marker )

class AbstractDocumentCompilerDriver(object):
	"""
	Accumulates resources into a single document which is compiled as a file;
	the compiler is expected to produce output files is that same directory.
	"""

	document_filename = 'resources'
	document_extension = 'tex'
	compiler = None

	def __init__(self, document, compiler='', encoding='utf-8', batch=0, **kwargs):
		self._document = document
		self._batch = batch
		self._writer = StringIO()
		if compiler:
			self.compiler = compiler
		self._encoding = encoding
		self._generatables = list()

	def __getstate__(self):
		# In concurrency, we need to be pickled. The plasTeX document
		# does not support this
		d = dict(self.__dict__)
		del d['_document']
		return d

	def size(self):
		return len(self._generatables)

	def writePreamble(self):
		pass #pragma: no cover

	def writePostamble(self):
		pass #pragma: no cover

	def _compilation_source_for_content_unit( self, content_unit ):
		"""
		Called to determine the source text (string) that represents the
		content unit during compilation. This implementation returns the
		`source` attribute of the given object (e.g., a :class:`plasTeX.DOM.Node`
		defines that attribute to return the TeX code to create that node).

		This is the appropriate place to add any wrapping or additional information that
		should be used during compilation of this unit.
		"""
		return content_unit.source

	def add_content_unit_to_batch(self, content_unit):
		# Recall that we cannot keep a proper reference to Node objects
		# during pickling. So we save the source only.
		# NOTE: Some of our subclasses are doing unholy things:
		# The ResourceDB lets us return a ContentRepresentation, which includes
		# the source used to generate it. That must match the source of the Node object
		# from the DOM in order for it to be found. Our subclasses depend on us
		# to track, in order, the original source (not the compiled source)
		self._generatables.append( content_unit.source )
		self.writeResource( self._compilation_source_for_content_unit( content_unit ) )

	def writeResource(self, source):
		self.write( source )

	def compile_batch_to_representations(self):

		start = time.time()

		workdir = self.compileSource()

		resources = self.create_resources_from_compiled_directory(workdir)
		nresources = len(resources)

		if nresources != len(self._generatables): # pragma: no cover
			logger.warn( 'Expected %s files but only generated %s for batch %s',
						 len(self._generatables), nresources, self._batch )

		elapsed = time.time() - start
		logger.info( "%s resources generated in %ss for batch %s", nresources, elapsed, self._batch )

		return resources

	def _run_compiler_on_file( self, filename ):
		"""
		:return: The exit status of the command.
		:raise subprocess.CalledProcessError: If the command fails
		"""
		# Run the compiler
		program = self.compiler
		# XXX This is fairly dangerous!
		#return os.system(r"%s %s" % (program, filename))
		return subprocess.check_call( (program, filename) )
		#JAM: This does not work. Fails to read input
		# cmd = str('%s %s' % (program, filename))
		# print shlex.split(cmd)
		# p = subprocess.Popen(shlex.split(cmd),
		# 			 stdout=subprocess.PIPE,
		# 			 stderr=subprocess.STDOUT,
		# 			 )
		# while True:
		# 	line = p.stdout.readline()
		# 	done = p.poll()
		# 	if line:
		# 		imagelogger.info(str(line.strip()))
		# 	elif done is not None:
		# 		break



	def compileSource(self):
		"""
		Writes the accumulated document to a file in a temporary directory, and then
		runs the compiler.
		:return: The name of the temporary directory.
		"""

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()

		filename = os.path.join(tempdir, self.document_filename + '.' + self.document_extension )

		self.source().seek(0)
		with codecs.open(filename,'w',self._encoding ) as out:
			out.write(self.source().read())

		try:
			self._run_compiler_on_file( filename )
		except:
			__traceback_info__ = self.source().getvalue()
			# TODO: See Imagers/__init__.py. Can we get log file info here?
			shutil.rmtree( tempdir, True ) # Try to clean up
			raise

		return tempdir


	def create_resources_from_compiled_directory(self, workdir):
		"""
		Given the directory in which the document was compiled,
		collect and return the generated resources.
		"""
		raise NotImplementedError( "Creating resources from compiled directory" ) #pragma: no cover

	def source(self):
		return self._writer

	def write(self, data):
		if data:
			self._writer.write(data)

class AbstractOneOutputDocumentCompilerDriver(AbstractDocumentCompilerDriver):
	"""
	Assumes the compiler creates one output document, looks for, and converts that.

	The output document is looked for based on the compiler document filename
	plus any one of the `output_extensions`.
	"""

	output_extensions = ('dvi','pdf','ps','xml') # The defaults are setup for tex

	def create_resources_from_compiled_directory(self, tempdir):

		output = None
		for ext in self.output_extensions:
			fname = self.document_filename + '.' + ext
			fpath = os.path.join(tempdir, fname)
			if os.path.isfile(fpath):
				output = WorkingFile(fpath, 'rb', tempdir=tempdir)
				break

		if output is None: # pragma: no cover
			__traceback_info__ = (self, tempdir, self.output_extensions)
			raise ValueError( "Compiler did not produce any output" )

		return self.convert(output, tempdir)

	def convert(self, output, workdir):
		"""
		Convert output to resources.
		:param output: An open file. When this file is closed, the temp directory will be deleted.
		:param workdir: The directory used by the compiler.
		:return: A sequence of content representation objects (resources).
		"""
		__traceback_info__ = self # pragma: no cover
		raise NotImplementedError # pragma: no cover

class AbstractLatexCompilerDriver(AbstractOneOutputDocumentCompilerDriver):
	"""
	Drives a compiler that takes latex input.
	"""

	interaction_mode = r'\batchmode'

	def writePreamble(self):
		self.write(self.interaction_mode)
		self.write( '\n' )

		self.write(getattr(self._document.preamble, 'source', self._document.preamble))
		self.write('\\makeatletter\\oddsidemargin -0.25in\\evensidemargin -0.25in\n')
		self.write('\\begin{document}\n')

	def writePostamble(self):
		self.write('\n\\end{document}\\endinput')

	def writeResource(self, source):
		self.write('%s\n%s\n' % ('', source))

class ImagerContentUnitRepresentationBatchConverterDriver(object):

	def __init__(self, imager, resourceType):
		self.imager = imager
		self.resourceType = resourceType

	def convert_batch(self, content_units):
		images = []
		for unit in content_units:
			# SAJ: Filter out options for includegraphics to prevent the loss of information from 
			# resizing the graphic and allow a single resource to be used for all references to a 
			# graphic.
			source = unit.source
			if 'includegraphics' in source or 'ntiincludeannotationgraphics' in source or 'ntiincludenoannotationgraphics' in source:
				if '[' in source and ']' in source:
					source = unit.source[:unit.source.index('[')] + unit.source[unit.source.index(']')+1:]

			#TODO newImage completely ignores the concept of imageoverrides
			new_image = self.imager.getImage(unit)
			#new_image = self.imager.newImage(source)
			if not interfaces.IContentUnitRepresentation.providedBy( new_image ):
				interface.alsoProvides( new_image, interfaces.IFilesystemContentUnitRepresentation )
				new_image.source = source
				new_image.qualifiers = ()
				new_image.resourceType = self.resourceType
				new_image.resourceSet = None
			images.append( new_image )

		self.imager.close()

		return images


class ImagerContentUnitRepresentationBatchConverter(AbstractContentUnitRepresentationBatchConverter):
	"""
	A batch converter that delegates to a plasTeX :class:`plasTeX.Imagers.Imager` object.

	Note that at this time, this object does not add concurrency. If concurrency is desired, it
	must be implemented integral to the imager.
	"""

	concurrency = 1
	imagerClass = None

	def __init__(self, document, imagerClass):
		super(ImagerContentUnitRepresentationBatchConverter, self).__init__(document)

		self.imagerClass = imagerClass
		if getattr(self.imagerClass,'resourceType', None):
			self.resourceType = self.imagerClass.resourceType
		else:
			self.resourceType = self.imagerClass.fileExtension[1:]

	def _new_batch_converter_driver(self, *args, **kwargs ):
		return ImagerContentUnitRepresentationBatchConverterDriver(self.createImager(), self.resourceType)

	def createImager(self):
		newImager = self.imagerClass(self.document)

		# create a tempdir for the imager to write images to
		tempdir = tempfile.mkdtemp()
		newImager.newFilename = Filenames(os.path.join(tempdir, 'img-$num(12)'),
										  extension=newImager.fileExtension)

		newImager._filecache = os.path.join(os.path.join(tempdir, '.cache'),
											newImager.__class__.__name__+'.images')

		return newImager
