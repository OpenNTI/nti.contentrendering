#!/usr/bin/env python

import os, sys
import plasTeX
from plasTeX.TeX import TeX

def toLaTeXDom(file):
	
	document = plasTeX.TeXDocument()
	
	#setup config options we want
	document.config['files']['split-level']=1
	document.config['general']['theme']='mathcounts'

	# Instantiate the TeX processor
	tex = TeX(document, file=file)

	# Populate variables for use later
	document.userdata['jobname'] = tex.jobname
	document.userdata['working-dir'] = os.getcwd()

	# parse
	tex.parse()

	return document

def toXml( document, outfile ):
	with open(outfile,'w') as f:
		f.write(document.toXML().encode('utf-8'))

if __name__ == '__main__':
	args = sys.argv[1:]
	print args
	if args:
		name = args[0]
		print name
		d = toLaTeXDom(name)
		toXml(d, name + ".xml")
