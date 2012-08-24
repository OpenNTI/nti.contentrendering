#!/usr/bin/env python

import os
import re
import sys
import time
from datetime import datetime
from xml.dom.minidom import parse
from xml.dom.minidom import Node

import lxml.etree as etree


from zope import interface

from whoosh import index

from concurrent.futures import ThreadPoolExecutor
from nti.contentrendering import interfaces
from nti.contentfragments.html import _sanitize_user_html_to_text
from nti.contentsearch.whoosh_contenttypes import create_book_schema

import whoosh.writing
import multiprocessing

from nltk import clean_html
from nltk.tokenize import RegexpTokenizer

import logging
logger = logging.getLogger(__name__)

interface.moduleProvides( interfaces.IRenderedBookTransformer )

name_anchor_pattern = re.compile(".+[#a\d+]$")
ref_pattern = re.compile("<span class=\"ref\">(.*)</span>")
last_m_pattern = re.compile("<meta content=\"(.*)\" http-equiv=\"last-modified\"")
page_c_pattern = re.compile("<div class=\"page-contents\">(.*)</body>")
default_tokenizer = RegexpTokenizer(r"(?x)([A-Z]\.)+ | \$?\d+(\.\d+)?%? | \w+([-']\w+)*",
									flags = re.MULTILINE | re.DOTALL | re.UNICODE)

def get_schema():
	return create_book_schema()

def get_or_create_index(indexdir, indexname, recreate=True):

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

def _get_related(node):
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

def parse_text(text, pattern, defValue=''):
	m = pattern.search(text, re.M|re.I)
	if m:
		return m.groups()[0]
	else:
		return defValue

def _parse_last_modified(t):
	result = time.time()
	try:
		if t:
			ms = ".0"
			idx = t.rfind(".")
			if idx != -1:
				ms = t[idx:]
				t = t[0:idx]

			t = time.strptime(t,"%Y-%m-%d %H:%M:%S")
			t = long(time.mktime(t))
			result = str(t) + ms
	except:
		pass	
	return float(result)
	
def get_last_modified(text):
	"""
	return the last modified date from the text
	"""
	t = parse_text(text, last_m_pattern, None)
	return _parse_last_modified(t)

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

def word_splitter(text, tokenizer=default_tokenizer):
	"""
	remove all html related tags and returs a list of words
	"""
	# user ds sanitizer
	text = _sanitize_user_html_to_text(text.lower())
	# remove any html (i.e. meta, link) that is not removed
	text = clean_html(text)
	# tokenize words
	words = tokenizer.tokenize(text)
	return words

def _index_node(writer, node, contentPath, optimize=False):
	"""
	Index a the information for a toc node
	"""

	attributes = node.attributes
	fileName = str(attributes['href'].value)
	if '#' in fileName: # file name ends with an anchor id
		return

	content_file = os.path.join(contentPath, str(fileName))
	if not os.path.exists(content_file):
		logger.warn("content file '%s' does not exists", content_file)
		return

	title = get_title(node)
	ntiid = get_ntiid(node)

	if not ntiid:
		return

	related = _get_related(node)

	logger.info( "Indexing (%s, %s, %s)", fileName, title, ntiid )

	with open(content_file, "r") as f:
		rawContent = f.read()

	section = get_ref(rawContent)
	last_modified = get_last_modified(rawContent)

	pageRawContent = get_page_content(rawContent)
	content = ' '.join(word_splitter(pageRawContent))

	keywords = set()
	try:
		as_time = datetime.fromtimestamp(float(last_modified))
		writer.add_document(ntiid=unicode(ntiid),
							title=unicode(title),
							content=unicode(content),
							quick=unicode(content),
							related=related,
							section=unicode(section),
							keywords=sorted(keywords),
							last_modified=as_time)
	except Exception:
		logger.exception( "Cannot index %s", content_file )
		writer.cancel()
		raise

def get_nodes(tocFile):
	dom = parse(tocFile)
	result = list()

	tocs = dom.getElementsByTagName("toc") # index
	if tocs and len(tocs) > 0:
		result.append(tocs[0])
		for topic in dom.getElementsByTagName("topic"):
			result.append(topic)

	return result


def main(tocFile,
		 contentPath=None,
		 indexdir=None,
		 indexname=None,
		 recreate_index=True,
		 optimize=True):
	"""
	Main program routine
	"""
	
	assert indexname, 'must provide an index name'
		
	if not contentPath:
		contentPath = os.path.dirname(tocFile)

	if not indexdir:
		indexdir = os.path.join(contentPath, "indexdir")
	
	# FIXME: Rewrite this process to use RenderedBook which has a better idea of what
	# constitutes a "page" to index
	nodes = get_nodes(tocFile)
	idx = get_or_create_index(indexdir, indexname, recreate=recreate_index)

	writer = whoosh.writing.BufferedWriter( idx,
											period=None,
											limit=100,
											commitargs={'optimize' : False, 'merge': False})

	with ThreadPoolExecutor(multiprocessing.cpu_count()) as pool:
		for node in nodes:
			pool.submit( _index_node, writer, node, contentPath)

	writer.commit()

	if optimize:
		logger.info( "Optimizing index" )
		idx.optimize()


index_content = main	

def _get_text(node):
	txt = node.text
	if txt:
		txt = unicode(txt.strip().lower())
	return txt
	
def _index_book_node(writer, node, tokenizer=default_tokenizer):
	title = unicode(node.title)
	ntiid = unicode(node.ntiid)
	related = _get_related(node.topic)
	
	# find last_modified
	last_modified = time.time()
	for n in node.dom('meta'):
		attributes = n.attrib
		if attributes.get('http-equiv', None) == "last-modified":
			last_modified = _parse_last_modified(attributes.get('content', None))
			break
		
	# get content
	content = []
	def _collector(n, lst):
		if not isinstance(n, etree._Comment):
			txt = _get_text(n)
			if txt:
				lst.append(txt)
			for c in n.iterchildren():
				_collector(c, lst)
			
	for n in node.dom("div").filter(".page-contents"):
		_collector(n, content)

	content = tokenizer.tokenize(' '.join(content))
	content = unicode(' '.join(content))

	# section has removed
	section = None
	
	#TODO: find key words
	keywords = set()
	
	try:
		as_time = datetime.fromtimestamp(float(last_modified))
		writer.add_document(ntiid=unicode(ntiid),
							title=unicode(title),
							content=unicode(content),
							quick=unicode(content),
							related=related,
							section=section,
							keywords=sorted(keywords),
							last_modified=as_time)
	except Exception:
		writer.cancel()
		raise	
	
def transform(book, indexname=None, indexdir=None, recreate_index=True, optimize=True):
	contentPath = book.contentLocation
	indexname = indexname or book.jobname
	if not indexdir:
		indexdir = os.path.join(contentPath, "indexdir")
		
	idx = get_or_create_index(indexdir, indexname, recreate=recreate_index)
	writer = whoosh.writing.BufferedWriter( idx,
											period=None,
											limit=100,
											commitargs={'optimize' : False, 'merge': False})
	
	toc = book.toc
	def _loop(topic):
		_index_book_node(writer, topic)
		for t in topic.childTopics:
			_loop(t)			
	_loop(toc.root_topic)
	
	if optimize:
		logger.info( "Optimizing index" )
		idx.optimize()


#from nti.contentrendering.tests import NoPhantomRenderedBook, EmptyMockDocument
#if __name__ == '__main__':
#	book = NoPhantomRenderedBook( EmptyMockDocument(), os.path.join( os.path.dirname( __file__ ),  'tests/intro-biology-rendered-book' ) )
#	transform(book, indexdir="/tmp/bio")

if __name__ == '__main__':
	def _call_main():
		args = sys.argv[1:]
		if args and len(args) >= 1:

			lm = lambda x,i: x[i] if len(x) > i else None
			toc_file = lm(args, 0)
			content_path = lm(args, 1)
			index_directory = lm(args, 2)
			index_name = lm(args, 3)

			main(toc_file, content_path, index_directory, index_name)
		else:
			print "Specify a toc-file [chapter-path] [index-directory] [index-name]"
	_call_main()
