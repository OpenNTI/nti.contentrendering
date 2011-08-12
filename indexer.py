#!/usr/bin/env python

import os
import re
import time
import sys
from datetime import datetime
from xml.dom.minidom import parse
from xml.dom.minidom import Node

from whoosh.fields import Schema, TEXT,ID, KEYWORD, DATETIME, STORED, NGRAM, NUMERIC
from whoosh import index

########

def getSchema():
	return Schema(	ntiid=ID(stored=True, unique=True),\
					title=TEXT(stored=True), 
				  	lastModified=DATETIME(stored=True),\
				  	keywords=KEYWORD(stored=True), \
				 	quick=NGRAM(maxsize=10),\
				 	related=STORED(),\
				 	ref=STORED(),\
				 	order=NUMERIC(int),\
				 	snippet=TEXT(stored=True),\
				  	content=TEXT(stored=False))
	
	
def getOrCreateIndex(indexdir, indexname ='prealgebra', recreate = True):
	
	if not os.path.exists(indexdir):
		os.makedirs(indexdir)
		recreate = True
		
	if not index.exists_in(indexdir, indexname=indexname):
		recreate = True
		
	if recreate:
		index.create_in(indexdir, schema=getSchema(), indexname=indexname)
	
	ix = index.open_dir(indexdir, indexname=indexname)
		
	return ix

########

ref_pattern = re.compile("<span class=\"ref\">(.*)</span>")
last_m_pattern = re.compile("<meta content=\"(.*)\" http-equiv=\"last-modified\"")
page_c_pattern = re.compile("<div class=\"page-contents\">(.*)</body>")

def getNTTID(node):
	attrs = node.attributes
	return attrs['ntiid'].value if attrs.has_key('ntiid') else None

def getTitle(node):
	attrs = node.attributes
	return attrs['label'].value if attrs.has_key('label') else None
	
def addNTTID2Set(set, node):
	ntiid = getNTTID(node)
	if ntiid:
		set.add(unicode(ntiid))
	return set

def getRelated(node):
	"""
	return a list w/ the related nttids for this node
	"""
	
	related = set()
	for child in node.childNodes:
		if child.nodeType == Node.ELEMENT_NODE:
			if child.localName == 'topic':
				addNTTID2Set(related, child)
			elif child.localName == 'Related':
				for c in child.childNodes:
					if c.nodeType == Node.ELEMENT_NODE and c.localName == 'page':
						addNTTID2Set(related, c)
			
	result = list(related)
	result.sort()
	return result

def parseText(text, pattern, defValue = ''): 
	m = pattern.search(text, re.M|re.I)
	if m: 
		return m.groups()[0]
	else:
		return defValue

def getLastModified(text):
	"""
	return the last modified date from the text
	"""
	now = time.time()
	
	t = parseText(text, last_m_pattern, None)
	try:
		if t:
			ms = ".0"
			idx = t.rfind(".")
			if idx != -1:
				ms = t[idx:]
				t = t[0:idx]
			
			t = time.strptime(t,"%Y-%m-%d %H:%M:%S")
			t = long(time.mktime(t))
			f = str(t) + ms
			return f
		else:
			return now;
	except:
		return now
	
def getRef(text):
	"""
	return the reference [chapter/section] code
	"""
	return parseText(text, ref_pattern)

def getPageContent(text):
	"""
	Returns everything after <div class="page-contents">
	"""
	c = text.replace('\n','')
	c = c.replace('\r','')
	c = c.replace('\t','')
	c = parseText(c, page_c_pattern, None)
	return c or text

def wordSplitter(text, wordpat=r"(?L)\w+"):
	"""
	remove all html related tags and returs a list of words
	"""
	text = text.lower()
	remove = [r"<[^<>]*>", r"&[A-Za-z]+;"]
	for pat in remove:
		text = re.sub(pat, " ", text)
	return re.findall(wordpat, text)

def getSnippet(text):
	"""
	Get the first paragraph with text in the specified content"
	"""
	s = re.sub("<p>","\n<p>", text)
	all = re.findall("<p>.*", s)
	for p in all:
		content = wordSplitter(p)
		content = ' '.join(content)
		if len(content) > 0:
			return content
	return ''

def indexNode(ix, node, contentPath, order = 0, optimize=False):
	"""
	Index a the information for a toc node
	TODO: How to get the keywords
	"""
	
	attributes = node.attributes
	fileName = str(attributes['href'].value)
	
	title = getTitle(node)
	ntiid = getNTTID(node)
	
	if not ntiid:
		return
	
	print "Indexing (%s, %s, %s)" % (fileName, title, ntiid)
		
	related = getRelated(node)
	
	contentFile = os.path.join(contentPath, str(fileName))
	with open(contentFile, "r") as f:
		rawContent = f.read() 
	
	ref = getRef(rawContent)
	lastModified = getLastModified(rawContent)
	
	pageRawContent = getPageContent(rawContent)
	snippet = getSnippet(pageRawContent)
	content = ' '.join(wordSplitter(pageRawContent))
		
	writer = ix.writer()
	
	try:
		asTime = datetime.fromtimestamp(float(lastModified))
		writer.add_document(ntiid=unicode(ntiid),\
							title=unicode(title),\
							content=unicode(content),\
							quick=unicode(content),\
							snippet=unicode(snippet),\
							related=related,\
							ref=ref,\
							order = order,\
							lastModified = asTime)
		
	except Exception, e:
		print "Cannot index %s,%s" % (contentFile,e)
		writer.cancel()

	writer.commit(merge=optimize, optimize=optimize)		
	
########				
					
def getNodes(tocFile):
	dom = parse(tocFile)
	result = list()
	
	tocs = dom.getElementsByTagName("toc") # index
	if tocs and len(tocs) > 0:
		result.append(tocs[0])
		for topic in dom.getElementsByTagName("topic"):
			result.append(topic)
			
	return result
	
def main(tocFile, contentPath, indexdir = None, indexname = "prealgebra"):
	""" Main program routine """
	
	if not indexdir:
		indexdir = os.path.join(contentPath, "indexdir")
		
	idx = getOrCreateIndex(indexdir, indexname)
	nodes = getNodes(tocFile)
	order = 0
	for node in nodes:
		indexNode(idx, node, contentPath, order)
		order += 1

	print "Optimizing index"
	
	idx.optimize()
	
if __name__ == '__main__':	
	
	args = sys.argv[1:]
	if args and len(args) >= 2:
		
		tocFile = args[0]
		contentPath = args[1]
		indexdir = args[2] if len(args) >= 3 else None
		indexname = args[3] if len(args) >= 4 else 'prealgebra'
		
		main(tocFile, contentPath, indexdir, indexname)
	else:
		print("Specify a toc-file chapter-path [index-directory] [index-name]")
		

