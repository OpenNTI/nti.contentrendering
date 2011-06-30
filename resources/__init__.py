#!/usr/bin/env python

import os, time, tempfile, shutil, re, string, cPickle, codecs, pdb
import subprocess, shlex, uuid
import copy as cp
import plasTeX.Imagers

try:
	from hashlib import md5
except ImportError:
	from md5 import new as md5

from StringIO import StringIO
from plasTeX.Logging import getLogger
from plasTeX.Filenames import Filenames
from plasTeX.dictutils import ordereddict
from plasTeX.Imagers import WorkingFile, Image

log = getLogger()
depthlog = getLogger('render.images.depth')
status = getLogger('status')
imagelog = getLogger('imager')

try:
	import Image as PILImage
	import ImageChops as PILImageChops
except ImportError:
	PILImage = PILImageChops = None

from collections import defaultdict

class Resource(object):

	def __init__(self, path, url=None, resourceSet=None, checksum=None):
		self.url = url
		self.path = path
		self.checksum = checksum
		self.resourceSet = resourceSet

	def __str__(self):
		return '%s' % self.path


#key digest cache
class CachingDigester(object):
	cachingEnabled = True

	digestCache = {}


	def digestKeys(self, toDigests):
		skeys = sorted(map(str, toDigests))
		dkey = ' '.join(skeys)

		return self.digest(dkey)

	def digest(self, toDigest):

		if toDigest in self.digestCache:
			return self.digestCache[toDigest]

		m = md5()
		m.update(toDigest)
		digest = str(m.hexdigest())

		if self.cachingEnabled:
			self.digestCache[toDigest] = digest

		return digest

digester = CachingDigester()

class ResourceSet(object):

	def __init__(self, source):
		self.resources = {}
		self.source = source
		self.path = digester.digest(source)

	def setResource(resource, keys):
		self.resources[digester.digestKeys(keys)] = resource

	def getResource(keys):
		if hasResource(keys):
			return self.resources[digester.digestKeys(keys)]
		return None

	def hasResource(keys):
		return digester.digestKeys(keys) in self.resources

	def __str__(self):
		return '%s' % self.resources
#ResourceSet

class ResourceDB(object):

	dirty = False



	types = {'mathjax_inline': 'tex2html',\
			 'mathjax_display': 'displaymath2html',\
			 'svg': 'pdf2svg',\
			 'png': 'gspdfpng2',\
			 'mathml': 'html2mathml'}

	"""
	Manages external resources (images, mathml, videos, etc..) for a document
	"""
	def __init__(self, document, path=None):
		self.__document=document
		self.__config=self.__document.config

		if not hasattr(Image, '_url'): # Not already patched
			Image._url=None
			def seturl(self, value):
				self._url=value

			def geturl(self):
				return self._url

			Image.url=property(geturl, seturl)

		if not path:
			path = 'resources'

		self.__dbpath=os.path.join(path, self.__document.userdata['jobname'])
		self.baseURL=self.__dbpath
		if not os.path.isdir(self.__dbpath):
			os.makedirs(self.__dbpath)

		print self.__dbpath

		log.info('Using %s as resource db' % self.__dbpath)

		self.__indexPath = os.path.join(self.__dbpath, 'resources.index')

		self.__db = {}

		self.__loadResourceDB()

	def __str__(self):
		return '%s'%self.__db


	def generateResourceSets(self):

		#set of all nodes we need to generate resources for
		nodesToGenerate=self.__findNodes(self.__document)

		#print nodesToGenerate

		#Generate a mapping of types to source  {png: [src2, src5], mathml: [src1, src5]}
		typesToSource=defaultdict(set)

		for node in nodesToGenerate:
			for rType in node.resourceTypes:
				# We don't want to regenerate for source that already esists
				if not node.source in self.__db or not rType in self.__db[node.source].resources:
					typesToSource[rType].add(node.source)

		print typesToSource

		for rType, sources in typesToSource.items():
			self.__generateResources(rType, sources)

		self.saveResourceDB()

	def __generateResources(self, resourceType, sources):
		#Load a resource generate
		generator=self.__loadGenerator(resourceType)

		if not generator:
			return

		print 'Generating %s resources' % resourceType
		generator.generateResources(sources, self)

	def __loadGenerator(self, resourceType):
		if not resourceType in self.types:
			log.warn('No generator specified for resource type %s' % resourceType)
			return None
		try:
			m  = __import__(self.types[resourceType])
			return m.ResourceGenerator(self.__document)
		except ImportError, msg:
			log.warning("Could not load custom imager '%s' because '%s'" % (resourceType, msg))
			return None

	def __findNodes(self, node):
		nodes=[]
		#print 'looking at node %s'%node
		if getattr(node, 'resourceTypes', None):
		#	print '****** Found resource types %s'%node.resourceTypes
			nodes.append(node)

		if getattr(node, 'attributes', None):
			for attrval in node.attributes.values():
				if getattr(attrval, 'childNodes', None):
					for child in attrval.childNodes:
						nodes.extend(self.__findNodes(child))

		for child in node.childNodes:
			nodes.extend(self.__findNodes(child))

		return list(set(nodes))


	def __loadResourceDB(self, debug = True):
		if os.path.isfile(self.__indexPath):
			try:
				print "Loading resource data from %s" % self.__indexPath

				self.__db = cPickle.load(open(self.__indexPath, 'r'))

				for key, value in self.__db.items():
					if debug:
						print "Checking key %s at %s" % (key, os.path.join(self.__dbpath,value.path))

					if not os.path.exists(os.path.join(self.__dbpath,value.path)):
						print 'Deleting resources for %s %s'% (key, os.path.join(self.__dbpath,value.path))
						del self.__db[key]
						continue
			except ImportError:
				print 'Error loading cache.  Starting from scratch'
				os.remove(self.__indexPath)
				self.__db={}
		else:
			self.__db={}

		print 'Loaded %s keys' % len(self.__db.keys())

	def setResource(self, source, keys, resource, debug = False):

		self.dirty = True

		if debug:
			print "Saving '%s', keys=%s, resource=.../%s" % (source, keys, str(resource)[-40:])

		if not source in self.__db:
			self.__db[source]=ResourceSet(source)

		resourceSet = self.__db[source]

		resourceSet.resources[digester.digestKeys(keys)] = self.__storeResource(resourceSet, keys, resource, debug)



	def __storeResource(self, rs, keys, origResource, debug = False):

		resource = cp.deepcopy(origResource)

		digest = digester.digestKeys(keys)
		name = '%s%s' % (digest, os.path.splitext(resource.path)[1])

		relativeToDB = os.path.join(rs.path, name)

		newpath = os.path.join(self.__dbpath, relativeToDB)
		copy(resource.path, newpath)
		resource.path = name
		resource.filename = name
		resource.resourceSet = rs
		resource.url = self.urlForResource(resource)

		if debug:
			print "\t=> url=%s" % resource.url

		return resource

	def urlForResource(self, resource):
		if self.baseURL and not self.baseURL.endswith('/'):
			self.baseURL='%s/'%self.baseURL

		if not self.baseURL:
			self.baseURL=''

		return '%s%s/%s'% (self.baseURL, resource.resourceSet.path, resource.path)



	def saveResourceDB(self):
		if not os.path.isdir(os.path.dirname(self.__indexPath)):
			os.makedirs(os.path.dirname(self.__indexPath))

		if not self.dirty:
			print 'Nothing to save'
			return

		print 'saving %s keys.' % len(self.__db.keys())
		cPickle.dump(self.__db, open(self.__indexPath,'w'))

	def __getResourceSet(self, source):
		if source in self.__db:
			return self.__db[source]
		return None

	def hasResource(self, source, keys):
		rsrcSet = self.__getResourceSet(source)

		if not rsrcSet:
			return None

		return rsrcSet.hasResource(keys)

	def getResourceContent(self, source, keys):
		path = self.getResourcePath(source, keys)
		if path:
			with codecs.open(path, 'r', 'utf-8') as f:
				return f.read()
		return None

	def getResource(self, source, keys):

		rsrcSet = self.__db[source]

		if rsrcSet == None:
			return None

		return rsrcSet.resources[digester.digestKeys(keys)]

	def getResourcePath(self, source, keys):
		rsrcSet = self.__getResourceSet(source)

		if not rsrcSet:
			return None


		digest = digester.digestKeys(keys)
		resourcePath = os.path.join(self.__dbpath, rsrcSet.path)

		for name in os.listdir(resourcePath):
			if name.startswith(digest):
				path = os.path.join(resourcePath, name)
				return path

		return None







#ResourceDB

class BaseResourceSetGenerator(object):

	def __init__(self, compiler='', encoding = '', batch=0):
		self.batch = batch
		self.writer = StringIO()
		self.compiler = compiler
		self.encoding = encoding
		self.generatables = list()

	def size(self):
		return len(self.generatables)

	def writePreamble(self, preamble):
		self.write('\\scrollmode\n')
		self.write(preamble)
		self.write('\\makeatletter\\oddsidemargin -0.25in\\evensidemargin -0.25in\n')
		self.write('\\begin{document}\n')

	def writePostamble(self):
		self.write('\n\\end{document}\\endinput')

	def addResource(self, s, context=''):
		self.generatables.append(s)
		self.writeResource(s, context)

	def writeResource(self, source, context):
		self.write('%s\n%s\n' % (context, source))

	def processSource(self):

		start = time.time()

		(output, workdir) = self.compileSource()

		resources = self.convert(output, workdir)
		nresources = len(resources)

		if nresources != len(self.generatables):
			print 'WARNING.	Expected %s files but only generated %s for batch %s' %\
				  (len(self.generatables), nresources, self.batch)

		elapsed = time.time() - start
		print "%s resources generated in %sms for batch %s" % (nresources, elapsed, self.batch)

		return zip(self.generatables, resources)

	def compileSource(self):

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()

		filename = os.path.join(tempdir,'resources.tex')

		self.source().seek(0)
		codecs.open(filename,\
					'w',\
					 self.encoding).write(self.source().read())

		# Run LaTeX
		os.environ['SHELL'] = '/bin/sh'
		program = self.compiler

		os.system(r"%s %s" % (program, filename))

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
		# 		imagelog.info(str(line.strip()))
		# 	elif done is not None:
		# 		break

		output = None
		for ext in ['.dvi','.pdf','.ps','.xml']:
			fpath = os.path.join(tempdir,'resources' + ext)
			if os.path.isfile(fpath):
				output = WorkingFile('resources' + ext, 'rb', tempdir=tempdir)
				break

		return (output, tempdir)

	def convert(self, output, workdir):
		"""
		Convert output to resources
		"""
		return []

	def source(self):
		return self.writer

	def writer(self):
		return self.writer

	def write(self, data):
		if data:
			self.writer.write(data)

#End BaseResourceSetGenerator

class BaseResourceGenerator(object):

	compiler = ''
	debug	 = False

	def __init__(self, document):
		self.document = document

	def storeKeys(self):
		return [self.resourceType]

	def context(self):
		return ''

	def createResourceSetGenerator(self, compiler='', encoding ='utf-8', batch = 0):
		return BaseResourceSetGenerator(self.document, compiler, encoding, batch)

	def generateResources(self, sources, db):

		generatableSources=[s for s in sources if self.canGenerate(s)]

		size = len(generatableSources)
		if not size > 0:
			print 'No sources to generate'
			return
		else:
			print 'Generating %s sources for %s' % (size, self.resourceType)

		encoding = self.document.config['files']['input-encoding']
		generator = self.createResourceSetGenerator(self.compiler, encoding)
		generator.writePreamble(self.document.preamble.source)
		for s in generatableSources:
			generator.addResource(s, self.context())
		generator.writePostamble()

		self.storeResources(generator.processSource(), db, self.debug)

	def storeResources(self, tuples, db, debug=False):
		for source, resource in tuples:
			if debug:
				print "%s -- %s" % (source, resource)
			db.setResource(source, self.storeKeys(), resource)

	def canGenerate(self, source):
		return True

#End BaseResourceSetGenerator

class ImagerResourceSetGenerator(BaseResourceSetGenerator):

	def __init__(self, imager, batch=0):
		super(ImagerResourceSetGenerator, self).__init__('', '', batch)
		self.imager = imager

	def writePreamble(self, preamble):
		pass

	def writePostamble(self):
		pass

	def writeResource(self, source, context):
		pass

	def processSource(self):
		images=[]
		for source in self.generatables:
			#TODO newImage completely ignores the concept of imageoverrides
			images.append(self.imager.newImage(source))

		self.imager.close()

		return zip(self.generatables, images)

	def compileSource(self):
		return (None, None)

	def convert(self, output, workdir):
		return []


#End ImagerResourceSetGenerator

class ImagerResourceGenerator(BaseResourceGenerator):

	concurrency = 1

	def __init__(self, document, imagerClass):
		super(ImagerResourceGenerator, self).__init__(document)

		self.imagerClass = imagerClass
		if getattr(self.imagerClass,'resourceType', None):
			self.resourceType = self.imagerClass.resourceType
		else:
			self.resourceType = self.imagerClass.fileExtension[1:]

	def createResourceSetGenerator(self, compiler='', encoding ='', batch = 0):
		return ImagerResourceSetGenerator(self.createImager(),  batch)

	def createImager(self):
		print 'creating imager from %s' % self.imagerClass
		newImager = self.imagerClass(self.document)

		#create a tempdir for the imager to right images to
		tempdir = tempfile.mkdtemp()
		newImager.newFilename=Filenames(os.path.join(tempdir, 'img-$num(4)'),\
									 	extension=newImager.fileExtension)

		newImager._filecache=os.path.join(os.path.join(tempdir, '.cache'),\
									   	  newImager.__class__.__name__+'.images')

		return newImager


#End ImagerResourceGenerator

def copy(source, dest, debug=True):

	if debug:
		print 'Copying %s to %s' % (source, dest)

	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		shutil.copy2(source, dest)
	except OSError:
		shutil.copy(source, dest)

#End copy




