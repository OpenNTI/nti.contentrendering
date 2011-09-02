#!/usr/bin/env python

import os
import re
import time
import sys
from datetime import datetime
from xml.dom.minidom import parse
from xml.dom.minidom import Node

from whoosh.fields import Schema, TEXT,ID, KEYWORD, DATETIME, NGRAM, NUMERIC
from whoosh import index

########

def get_schema():
	return Schema(	ntiid=ID(stored=True, unique=True),\
					title=TEXT(stored=True, spelling=True), 
				  	last_modified=DATETIME(stored=True),\
				  	keywords=KEYWORD(stored=True), \
				 	quick=NGRAM(maxsize=10),\
				 	related=KEYWORD(),\
				 	section=TEXT(),\
				 	order=NUMERIC(int),\
				  	content=TEXT(stored=True, spelling=True))
	
	
def get_or_create_index(indexdir, indexname ='prealgebra', recreate = True):
	
	if not os.path.exists(indexdir):
		os.makedirs(indexdir)
		recreate = True
		
	if not index.exists_in(indexdir, indexname=indexname):
		recreate = True
		
	if recreate:
		ix = index.create_in(indexdir, schema=get_schema(), indexname=indexname)
	else:
		ix = index.open_dir(indexdir, indexname=indexname)
		
	return ix

########

ref_pattern = re.compile("<span class=\"ref\">(.*)</span>")
last_m_pattern = re.compile("<meta content=\"(.*)\" http-equiv=\"last-modified\"")
page_c_pattern = re.compile("<div class=\"page-contents\">(.*)</body>")

def get_ntiid(node):
	attrs = node.attributes
	return attrs['ntiid'].value if attrs.has_key('ntiid') else None

def get_title(node):
	attrs = node.attributes
	return attrs['label'].value if attrs.has_key('label') else None
	
def add_ntiid_to_set(pset, node):
	ntiid = get_ntiid(node)
	if ntiid:
		pset.add(unicode(ntiid))
	return pset

def get_related(node):
	"""
	return a list w/ the related nttids for this node
	"""
	
	related = set()
	for child in node.childNodes:
		if child.nodeType == Node.ELEMENT_NODE:
			if child.localName == 'topic':
				add_ntiid_to_set(related, child)
			elif child.localName == 'Related':
				for c in child.childNodes:
					if c.nodeType == Node.ELEMENT_NODE and c.localName == 'page':
						add_ntiid_to_set(related, c)
			
	result = list(related)
	result.sort()
	return result

def parse_text(text, pattern, defValue = ''): 
	m = pattern.search(text, re.M|re.I)
	if m: 
		return m.groups()[0]
	else:
		return defValue

def get_last_modified(text):
	"""
	return the last modified date from the text
	"""
	now = time.time()
	
	t = parse_text(text, last_m_pattern, None)
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
	
def get_ref(text):
	"""
	return the reference [chapter/section] code
	"""
	return parse_text(text, ref_pattern)

def get_page_content(text):
	"""
	Returns everything after <div class="page-contents">
	"""
	c = text.replace('\n','')
	c = c.replace('\r','')
	c = c.replace('\t','')
	c = parse_text(c, page_c_pattern, None)
	return c or text

def word_splitter(text, wordpat=r"(?L)\w+"):
	"""
	remove all html related tags and returs a list of words
	"""
	text = text.lower()
	remove = [r"<[^<>]*>", r"&[A-Za-z]+;"]
	for pat in remove:
		text = re.sub(pat, " ", text)
	return re.findall(wordpat, text)

def get_first_paragraph(text):
	"""
	Get the first paragraph with text in the specified content"
	"""
	s = re.sub("<p>","\n<p>", text)
	hits = re.findall("<p>.*", s)
	for p in hits:
		content = word_splitter(p)
		content = ' '.join(content)
		if len(content) > 0:
			return content
	return ''

def index_node(ix, node, contentPath, order = 0, optimize=False):
	"""
	Index a the information for a toc node
	TODO: How to get the keywords
	"""
	
	attributes = node.attributes
	fileName = str(attributes['href'].value)
	
	title = get_title(node)
	ntiid = get_ntiid(node)
	
	if not ntiid:
		return
	
	print "Indexing (%s, %s, %s)" % (fileName, title, ntiid)
		
	related = get_related(node)
	
	contentFile = os.path.join(contentPath, str(fileName))
	with open(contentFile, "r") as f:
		rawContent = f.read() 
	
	section = get_ref(rawContent)
	last_modified = get_last_modified(rawContent)
	
	pageRawContent = get_page_content(rawContent)
	content = ' '.join(word_splitter(pageRawContent))
		
	writer = ix.writer()
	
	try:
		as_time = datetime.fromtimestamp(float(last_modified))
		writer.add_document(ntiid=unicode(ntiid),\
							title=unicode(title),\
							content=unicode(content),\
							quick=unicode(content),\
							related=related,\
							section=unicode(section),\
							order=order,\
							last_modified=as_time)
		
	except Exception, e:
		print "Cannot index %s,%s" % (contentFile,e)
		writer.cancel()

	writer.commit(merge=optimize, optimize=optimize)		
	
########				
					
def get_nodes(tocFile):
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
		
	idx = get_or_create_index(indexdir, indexname)
	nodes = get_nodes(tocFile)
	order = 0
	for node in nodes:
		index_node(idx, node, contentPath, order)
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
		

