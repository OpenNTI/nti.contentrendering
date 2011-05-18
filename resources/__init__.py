#!/usr/bin/env python

import os, time, tempfile, shutil, re, string, pickle, codecs, pdb
try: from hashlib import md5
except ImportError: from md5 import new as md5
from plasTeX.Logging import getLogger
from StringIO import StringIO
from plasTeX.Filenames import Filenames
from plasTeX.dictutils import ordereddict
import subprocess
import shlex
import plasTeX.Imagers
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
	def __init__(self, filename):
		self.filename=filename
		self.path = os.path.join(os.getcwd(), self.filename)
		self.checksum=None

class ResourceSet(object):
	def __init__(self, path, source):
		self.path=path
		self.resources={}
		self.source=source
	def getTypes(self):
		return resources.keys()
	def __str__(self):
		return '%s' % self.resources

import uuid
class ResourceDB(object):

	types = {'svg': 'pdf2svg', 'png': 'gspdfpng2', 'mathml': 'html2mathml'}

	"""
	Manages external resources (images, mathml, videos, etc..) for a document
	"""
	def __init__(self, document, path=None):
		self.__document=document
		self.__config=self.__document.config
		if not path:
			path = 'resources'

		self.__dbpath=os.path.join(path, self.__document.userdata['jobname'])

		if not os.path.isdir(self.__dbpath):
			os.makedirs(self.__dbpath)

		log.info('Using %s as resource db' % self.__dbpath)

		self.__indexPath = os.path.join(self.__dbpath, 'resources.index')

		self.__loadResourceDB()

		self.__generateResourceSets()

		self.__saveResourceDB()

	def __str__(self):
		return '%s'%self.__db

	def getResourceSet(self, node):
		if node.source in self.__db:
			return self.__db[node.source]
		else:
			return None

	def __generateResourceSets(self):

		#set of all nodes we need to generate resources for
		nodesToGenerate=self.__findNodes(self.__document)

		#print nodesToGenerate

		#Each unique source gets a resourceset
		for node in nodesToGenerate:
			if not node.source in  self.__db:
				self.__db[node.source]=ResourceSet(os.path.join(self.__dbpath,str(uuid.uuid1())), node.source)
		#Generate a mapping of types to source  {png: [src2, src5], mathml: [src1, src5]}
		typesToSource=defaultdict(set)



		for node in nodesToGenerate:
			resourceset=self.__db[node.source]
			for rType in node.resourceTypes:
				if not rType in resourceset.resources:
					typesToSource[rType].add(node.source)

		print typesToSource

		for rType, sources in typesToSource.items():
			self.__generateResources(rType, sources)

	def __generateResources(self, type, sources):
		#Load a resource generate
		generator=self.__loadGenerator(type)

		if not generator:
			return


		resourcesets=[rset for rset in self.__db.values() if rset.source in sources]

		generator.generateResources(self.__document, resourcesets)

	def __loadGenerator(self, type):
		if not type in self.types:
			log.warn('No generator specified for resource type %s' % type)
			return None
		try:
			exec('from %s import ResourceGenerator' % self.types[type])
			return ResourceGenerator(self.__document)
		except ImportError, msg:
			log.warning("Could not load custom imager '%s' because '%s'" % (type, msg))
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


	def __loadResourceDB(self):
		if os.path.isfile(self.__indexPath):
			try:
				self.__db = pickle.load(open(self.__indexPath, 'r'))
				for key, value in self.__db.items():
					if not os.path.exists(value.path):
						print 'Deleting resources for %s %s'% (key, value.path)
						del self.__db[key]
						continue
			except ImportError:
				print 'Error loading cache.  Starting from scratch'
				os.remove(self.__indexPath)
				self.__db={}
		else:
			self.__db={}

	def __saveResourceDB(self):
		if not os.path.isdir(os.path.dirname(self.__indexPath)):
			os.makedirs(os.path.dirname(self.__indexPath))
		pickle.dump(self.__db, open(self.__indexPath,'w'))



#We need to add caching so we don't regenerate from run to run.  We also
#need to key images by source so we don't
#generate duplicate images

class BaseResourceGenerator(object):

	compiler = ''


	def __init__(self,document):
		self.document=document

	def generateResources(self, document, resourcesets):
		self.source = StringIO()
		self.source.write('\\scrollmode\n')
		self.writePreamble(document)
		self.source.write('\\begin{document}\n')

		generatableResources=[rset for rset in resourcesets if self.canGenerate(rset.source)]

		if not len(generatableResources)>0:
			print 'No resources to generate'
			return

		for rset in generatableResources:
			self.writeResource(rset.source, '')

		self.source.write('\n\\end{document}\\endinput')

		output = self.compileSource()

		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)

		resources=self.convertOutput(output)

		os.chdir(cwd)

		for resource, rset in zip(resources, generatableResources):
			finalPath=os.path.join(rset.path, resource)
			copy(os.path.join(tempdir, resource), os.path.join(rset.path, resource))
			rset.resources[self.resourceType]=finalPath

	def writePreamble(self, document):
		self.source.write(document.preamble.source)
		self.source.write('\\makeatletter\\oddsidemargin -0.25in\\evensidemargin -0.25in\n')




	def writeResource(self, source, context):
		self.source.write('%s\n%s\n' % (context, source))

	def compileSource(self):
		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)

		filename = 'resources.tex'

		self.source.seek(0)
		codecs.open(filename, 'w', self.document.config['files']['input-encoding']).write(self.source.read())

		# Run LaTeX
		os.environ['SHELL'] = '/bin/sh'
		program  = self.compiler


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
			if os.path.isfile('resources'+ext):
				output = WorkingFile('resources'+ext, 'rb', tempdir=tempdir)
				break

		os.chdir(cwd)

		return output


	def convertOutput(self, output):
		pass

	def canGenerate(self, source):
		return True

class ResourceGenerator(BaseResourceGenerator):



	def __init__(self,document, imagerClass):
		self.document=document
		self.imagerClass=imagerClass
		if getattr(self.imagerClass,'resourceType', None):
			self.resourceType = self.imagerClass.resourceType
		else:
			self.resourceType = self.imagerClass.fileExtension[1:]



	#Given a document and a set of sources generate a map of source -> map of type to plastex image obj
	def generateResources(self, document, resourcesets):
		"""
		The first pass collects the latex source for each of the
		provided nodes.  A latex file is generated from the collected source and compiled.  The compiled latex
		is passed to the imager and the the list of generated images are returned.  The images are stored on disk
	    in the path provided by the resource set and noted as appropriate
		"""

		generatableResources=[rset for rset in resourcesets if self.canGenerate(rset.source)]

		#create a new imager
		imager=self.imagerClass(document)

		images=[]

		for rset in generatableResources:
			#TODO newImage completely ignores the concept of imageoverrides
			images.append(imager.newImage(rset.source))

		imager.close()



		for rset, image in zip(generatableResources, images):
			name=os.path.basename(image.path)
			newPath=os.path.join(rset.path, name)
			copy(image.path, newPath)
			image.filename=name
			image.path=newPath
			rset.resources[self.resourceType]=image




def copy(source, dest):
	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		shutil.copy2(source, dest)
	except OSError:
		shutil.copy(source, dest)




