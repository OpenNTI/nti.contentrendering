#!/usr/bin/env python

import os,tempfile, re, tempfile
from plasTeX.Logging import getLogger
import plasTeX.Imagers
import glob
import sys

from concurrent.futures import ProcessPoolExecutor
from nti.contentrendering.resources import converters, interfaces
from zope import interface


log = getLogger(__name__)
depthlog = getLogger('render.images.depth')
status = getLogger('status')
imagelog = getLogger('imager')

import plasTeX.Imagers
from plasTeX.Imagers import Image
import subprocess
import math

status = getLogger('status')

gs = 'gs'
if sys.platform.startswith('win'):
	gs = 'gswin32c'

import plasTeX.Imagers.gspdfpng

## def _size(page,key):
## 	width_in_pt, height_in_pt = subprocess.Popen( "pdfinfo -box -f %d images.out | grep MediaBox | awk '{print $4,$5}'" % (page), shell=True, stdout=subprocess.PIPE).communicate()[0].split()
## 	return (key, width_in_pt, height_in_pt)

def _size(key, png):
	width_in_pt, height_in_pt = subprocess.Popen( "identify %s | awk '{print $3}'" % (png), shell=True, stdout=subprocess.PIPE).communicate()[0].split('x')
	return (key, width_in_pt, height_in_pt)

def _scale(input, output, scale, defaultScale):
	# Use IM to scale. Must be top-level to pickle
	#scale is 1x, 2x, 4x
	return os.system( 'convert %s -resize %d%% PNG32:%s' % (input, 100*(scale/defaultScale) , output) )

class GSPDFPNG2(plasTeX.Imagers.gspdfpng.GSPDFPNG):
	""" Imager that uses gs to convert pdf to png, using PDFCROP to handle the scaling """
	command = ('%s -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha ' % gs) + \
			  '-dGraphicsAlphaBits=4 -sOutputFile=img%d.png'
	compiler = 'pdflatex'
	fileExtension = '.png'
	size = 500
	scaleFactor = 1
	defaultScaleFactor = 4.0

	def executeConverter(self, output):
		open('images.out', 'wb').write(output.read())
		# Now crop
		# We complain about images being raised above the baseline, yet we have the margin set to 3?
		#os.system( "pdfcrop --hires --margin 3 images.out images.out" )
		#os.system( "pdfcrop --hires images.out images.out" )
		# pdfcrop produces useless stdout data
		with open('/dev/null', 'w') as dev_null:
			subprocess.check_call( ('pdfcrop', '--hires', 'images.out', 'images.out' ),
								   stdout=dev_null, stderr=dev_null )

		#maxpages = int(subprocess.Popen( "pdfinfo images.out | grep Pages | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).communicate()[0])
		# Record the fact that we've cropped them (in parallel, getting the size takes time)
		## with ProcessPoolExecutor() as executor:
		## 	for the_tuple in executor.map( _size, xrange(1, maxpages + 1 ), self.images.keys() ):
		## 		img = self.images[the_tuple[0]]
		## 		img._cropped = True
		## 		img.width = math.ceil( float(the_tuple[1]) ) * 1.3
		## 		img.height = math.ceil( float(the_tuple[2]) ) * 1.3
		## 		img.depth = -3
		## 	# TODO: This is in points, we want it in pixels; these are
		## 	# coming in too small
		## 	# We're arbitrarily assigning a height above baseline to match the margin

		options = ''
		if self._configOptions:
			for opt, value in self._configOptions:
				opt, value = str(opt), str(value)
				if ' ' in value:
					value = '"%s"' % value
				options += '%s %s ' % (opt, value)

		res = os.system('%s -r%d %s%s' % (self.command, self.size ,options, 'images.out')), None




		if self.scaleFactor != None:
			self.scaleImages()

		pngs = glob.glob('img*.png')
		pngs.sort(lambda a,b: cmp(int(re.search(r'(\d+)\.\w+$',a).group(1)),
									int(re.search(r'(\d+)\.\w+$',b).group(1))))

		# Record the fact that we've cropped them (in parallel, getting the size takes time)
		with ProcessPoolExecutor() as executor:
			for the_tuple in executor.map( _size, self.images.keys(), pngs ):
				img = self.images[the_tuple[0]]
				img._cropped = True
				img.width = math.ceil( float(the_tuple[1]) ) / 1.3
				img.height = math.ceil( float(the_tuple[2]) ) / 1.3
				#img.depth = -3

		return res

	def writePreamble( self, document ):
		""" Because we do our own cropping, we don't need the registration mark. Hence, we define that to do nothing; the
		superclass then does NOT define it. """
		self.source.write( "\\newcommand{\plasTeXregister}{}" )
		super(GSPDFPNG2,self).writePreamble( document )

	def scaleImages(self):
		" Uses ImageMagick to scale the images in parallel "
		with ProcessPoolExecutor() as executor:
			pngs = glob.glob('img*.png')
			for _ in executor.map( _scale, pngs, pngs, [self.scaleFactor for x in pngs], [self.defaultScaleFactor for x in pngs]):
				pass


def _invert(input, output):
	return os.system('convert %s -negate %s' % (input, output))

Imager = GSPDFPNG2

from ._util import copy


class ResourceGenerator(converters.ImagerContentUnitRepresentationBatchConverter):

	scales = (1,)
	shouldInvert = False

	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document, Imager)

	def process_batch(self, content_units):

		rsg = self._new_batch_converter_driver()
		rsg.imager.scaleFactor = None  #We scale them on our side

		sources = [content_unit.source for content_unit in content_units]

		processed = rsg.convert_batch( sources )

		#origSources, origImages = zip(*processed)
		#origImages = processed

		#Create a tempdir to work in
		tempdir = tempfile.mkdtemp()

		imagesToResizeSource = []
		imagesToResizeDest = []

		allNewImages = []

		for image in processed:
			source = image.source
			if image is None or image.width is None or image.height is None:
				raise Exception( "Unable to generate image for '%s' (%s)" % (source, image) )
			for scale in self.scales:
			   	newImage = self.makeImage( os.path.join( tempdir,
														 self.__newNameFromOrig(image.path,
																				scale,
																				False)),
											image.width * (scale / rsg.imager.defaultScaleFactor),
											image.height * (scale/rsg.imager.defaultScaleFactor),
											image.depth )

				newImage._scaleFactor = scale
				newImage._source = source
				newImage.source = source
				newImage.qualifiers = ('orig', scale) # TODO: We should define a named tuple class for our qualifiers
				interface.alsoProvides( newImage, interfaces.IContentUnitRepresentation )
				allNewImages.append(newImage)

				#Simple copy
				if newImage._scaleFactor == rsg.imager.defaultScaleFactor:
					copy(image.path, newImage.path)
				else:
					imagesToResizeSource.append(image)
					imagesToResizeDest.append(newImage)


		#Do the resize
		with ProcessPoolExecutor() as executor:
			for _ in executor.map( _scale,
								   [image.path for image in imagesToResizeSource],
								   [image.path for image in imagesToResizeDest],
								   [image._scaleFactor for image in imagesToResizeDest],
								   [rsg.imager.defaultScaleFactor for x in imagesToResizeSource] ):
				pass



		#Now invert
		allInvertedImages = []
		if self.shouldInvert:
			for scale in self.scales:
				for origImage in allNewImages:
					newImage = self.makeImage( os.path.join( tempdir,
															 self.__newNameFromOrig(origImage.path,
																					scale,
																					True)),
												origImage.width,
												origImage.height,
												origImage.depth )
					newImage.source = origImage.source
					newImage.qualifiers = ('inverted', scale)
					interface.alsoProvides( newImage, interfaces.IContentUnitRepresentation )
					allInvertedImages.append(newImage)

			with ProcessPoolExecutor() as executor:
				for _ in executor.map(_invert, [image.path for image in allNewImages], [image.path for image in allInvertedImages]):
					pass


		return allNewImages + allInvertedImages


	def makeImage(self, path, width, height, depth, cropped=True):
		image = Image(os.path.basename(path), None)
		# TODO: This is something of an abuse of things. We use this as a
		# Resource object even though it isn't really.
		image.path = path
		image.width = width
		image.height = height
		image.depth = depth
		image._cropped = cropped
		return image

	def __newNameFromOrig(self, name, size, inverted):
		dir, base = os.path.split(name)
		fname, ext = os.path.splitext(base)

		newName = '%s_%dx' % (fname, size)

		if inverted:
			newName += '_inverted'

		newName += '%s' % ext

		return newName