#!/usr/bin/env python

import os, sys
from json import JSONEncoder
import plasTeX
from plasTeX.TeX import TeX


def _parseLaTeX(file):
	
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
# End _parseLaTeX

def todict(file):
	"""
	Return a python dictionary from the specified LaTeX file
	"""
	return _todict(_parseLaTeX(file))
	
def _todict(document):
	"""
	Return a python dictionary from the specified plasTeX document
	"""
	result = dict()
	result['Items'] = items = dict()
	
	questionId = 1
	for question in document.getElementsByTagName( 'question' ):
		
		answers = list()
		problemSource = None
		
		for problem in question.getElementsByTagName("problem"):			
			problemSource = problem.source
			# break since we should have only one problem per question
			break
			
		for solution in question.getElementsByTagName("solution"):
			answers.append(solution.source)
			
		if problemSource and answers:
			qsid = str(questionId)
			items[qsid] = (qsid, problemSource, answers)
			
		questionId = questionId + 1
	
	return result

def toJSON(file):
	"""
	Return a JSON string from the specified LaTeX file
	"""
	return _toJSON(_parseLaTeX(file))
	
def _toJSON(document):
	"""
	Return a JSON string from the specified plasTeX document
	"""
	return JSONEncoder().encode(_todict(document))

def toXml( file, outfile = None ):
	"""
	Save the specified LaTeX file to a plasTeX xml file
	"""
	if not outfile:
		t = os.path.splitext(file)
		outfile = '%s.xml' % t[0]
	
	document = _parseLaTeX(file)
	with open(outfile,'w') as f:
		f.write(document.toXML().encode('utf-8'))
		
	return outfile

def transform(file, format='json', outfile = None):
	
	if format == 'xml':
		return toXml(file, outfile)
	elif format == 'json':
		json = toJSON(file)
		
		if outfile:
			with open(outfile,'w') as f:
				f.write(json)
		
		return json
	else:
		return None
	
def put(file, url):
	"""
	Put the json representation of the specified LaTeX file in the specified url
	"""
	import urllib2
	
	json = toJSON(file)
	
	opener = urllib2.build_opener(urllib2.HTTPHandler)
	request = urllib2.Request(url, data=json)
	request.add_header('Content-Type', 'application/json')
	request.get_method = lambda: 'PUT'
	
	return opener.open(request)

def put2(file, url):
	"""
	Put the json representation of the specified LaTeX file in the specified url
	"""
	import httplib
	from urlparse import urlparse

	pr = urlparse(url)
	server = pr.netloc
	path = pr.path

	connection =  httplib.HTTPConnection(server)
	json = toJSON(file)
	connection.request('PUT', path, json)
	
	return connection.getresponse()
	
if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		put2(args[0], 'http://www.nt.com/dataserver/carlos/qid')
		
		
		