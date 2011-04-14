#!/usr/bin/env python

from plasTeX.Logging import getLogger
import plasTeX.Imagers, glob, sys, os

status = getLogger('status')

gs = 'gs'
if sys.platform.startswith('win'):
   gs = 'gswin32c'

import plasTeX.Imagers.gspdfpng

class GSPDFPNG2(plasTeX.Imagers.gspdfpng.GSPDFPNG):
	""" Imager that uses gs to convert pdf to png, using PDFCROP to handle the scaling """
	command = ('%s -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r250 ' % gs) + \
			  '-dGraphicsAlphaBits=4 -sOutputFile=img%d.png'
	compiler = 'pdflatex'
	fileExtension = '.png'

	def executeConverter(self, output):
		open('images.out', 'wb').write(output.read())
		# Now crop it
		print 'croping'
		os.system( "pdfcrop --hires --margin 3 images.out images.out" )
		options = ''
		if self._configOptions:
			for opt, value in self._configOptions:
				opt, value = str(opt), str(value)
				if ' ' in value:
					value = '"%s"' % value
				options += '%s %s ' % (opt, value)

		return os.system('%s %s%s' % (self.command, options, 'images.out')), None


Imager = GSPDFPNG2
