#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Partial support for the amsopn package

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re

from zope import interface

from nti.contentrendering import plastexids
from nti.contentrendering.resources.interfaces import IRepresentationPreferences

from nti.contentrendering.plastexpackages.picins import parpic
from nti.contentrendering.plastexpackages.picins import picskip
from nti.contentrendering.plastexpackages.amsopn import DeclareMathOperator

from plasTeX import Base
from plasTeX import Command
from plasTeX.Base import Node
from plasTeX.Base import Crossref
from plasTeX.Base.LaTeX import Index
from plasTeX.Packages import graphicx

###
# FIXME: star imports!
# If we don't, then we wind up with some rendering problems (at least the following):
# - unable to traverse to 'url' on an includegraphics
# - "No resource types for align* using default renderer <type 'unicode'>"
###
from plasTeX.Packages.amsmath import *
from plasTeX.Packages.fancybox import *
from plasTeX.Packages.graphicx import *


# Disable pylint warning about "too many methods" on the Command subclasses,
# and "deprecated string" module
# pylint: disable=R0904,W0402

class _OneText(Base.Command):
	args = 'text:str'

	def invoke( self, tex ):
		return super(_OneText, self).invoke( tex )

class _Ignored(Base.Command):
	unicode = ''

	def invoke( self, tex ):
		return []

# Presentation things to ignore

class rindent(_Ignored):
	pass

class vupnud(_Ignored):
	pass

class pagebreak(_Ignored):
	pass

# TODO: In many cases phantom is used purely for spacing we don't care about
# in our rendering.  At other times it's used for spaceing we do need to render (e.g. fill in the blank style blanks)
# This looks like it will be a case by case basis.
# included phantom doesn't allow for tex fragments as args
class phantom(Base.Space.phantom):
	args = 'tex'

@interface.implementer(IRepresentationPreferences)
class Cube(_OneText):
	resourceTypes = ['png', 'svg']

class BlackCube(Cube):
	pass

# Parses the \multicols environment and produces no output.  The childred of
# this environment print as if they were not inside the multicols environment.
class multicols(Base.Environment):
	args = ' {text:int} '

	def invoke( self, tex ):
		# There's a {0} or so with this that we need to discard too
		# TODO: This may not be the best way
		tex.readGrouping( '{}' )
		return []

	def digest( self, tokens ):
		return super(multicols,self).digest( tokens )

# class newline(Base.Command):
#	macroName = '\\'

#	def toXML(self):
#		return '<newline/>'

def digestUntilNextTextSize(self, tokens):
	return _digestAndCollect( self, tokens, Base.FontSelection.TextSizeDeclaration )

Base.FontSelection.TextSizeDeclaration.digest = digestUntilNextTextSize

class rule(Base.Boxes.rule):
	""" Rules have no place in this DOM, except in math mode, where their presentation
	can be important (e.g., the rlin macro)."""
	def invoke( self, tex ):
		superResult = super(rule,self).invoke( tex )
		if self.ownerDocument.context.isMathMode:
			if self.ownerDocument.context.contexts[-1].parent.name == 'array':
				# One exception is when they use rules inside arrays
				# to try to extend an hline. mathjax rendering doesn't
				# need this, and I didn't see it being helpful in
				# their PDF either
				return []
			return superResult
		return []

class vspace(Base.Space.vspace):

	def invoke( self, tex ):
		super( vspace, self ).invoke( tex )
		return []

class vskip(Base.Primitives.vskip):

	def invoke( self, tex ):
		super( vskip, self ).invoke( tex )
		return []

class chapterpicture(_OneText):

	def invoke( self, tex ):
		super(chapterpicture,self).invoke( tex )
		return []

# FIXME: Chapterauthor and chapterquote are included
# BEFORE the \chapter marker, and so get digested into the
# PREVIOUS section in the DOM, not the chapter they belong too.
# Maybe these can just be discarded?

class chapterquote(Base.Command):
	args = ''
	blockType = True

	def invoke( self, tex ):
		#TODO: Can we read the next command, which should be the
		#\chapterauthor and add that as a child node?
		tokens, _ = tex.readGrouping( '{}', expanded=True, parentNode=self)
		self += tokens
		return None

class chapterauthor(Base.Command):
	args = ''
	blockType = True

	def invoke( self, tex ):
		self += tex.readGrouping( '{}', expanded=True, parentNode=self)[0]
		return None


class Def(_OneText):
	pass

class Defnoindex(_OneText):
	args = 'text'

class defn(Base.Environment):
	blockType = True

class defns(Base.Environment):
	blockType = True

class picdefns(defns):
	args = '{Picture}'

class cancel(Base.Command):
	args = 'text'

class cancelto(Base.Command):
	args = 'to text'

#TODO:  Inherit from something in Boxes.py?
class boxed(Base.Command):
	args = '{self}'

class text(Base.BoxCommand):

	args = '{self}'

	def __init__(self):
		super(text,self).__init__()
		self.arguments[0].options['stripLeadingWhitespace'] = True

# TODO: does this get handled like ^
class textsuperscript(Base.Command):
	args = 'text:str'

# We would like to be able to normalize math mode
# at parse time such that expressions like $24$ automatically
# become simple text nodes, but that's not (easily) possible: we cannot
# make that decision until after the children are parsed, and by then
# we're in the DOM (the digest() method does not yet have the proper parentNode)
# to remove

class angle(Base.Command):

	def invoke( self, tex ):
		super(angle, self).invoke(	tex )

# The rlin command and the vv command break rendering of
# vectors, so they are disabled.
# class rlin(Base.Command):
#	""" A presentation command that means overleftrightarrow """
#	args = ''

#	def invoke( self, tex ):
#		arrow = self.ownerDocument.createElement( 'overleftrightarrow' )
#		expr = tex.readGrouping( '{}', expanded=True, parentNode=arrow)[0]
#		arrow += expr
#		return [arrow]

#class vv(Base.Command):
#	""" A vector from esvect. We simplify to the common overrightarrow """
#
#	args = ''
#
#	def invoke( self, tex ):
#		arrow = self.ownerDocument.createElement( 'vec' )
#		expr = tex.readGrouping( '{}', expanded=True, parentNode=arrow)[0]
#		arrow += expr
#		return [arrow]

# rlin is re-enabled for the sake of mathjax
class rlin(Base.Command):
	""" 
	A presentation command that means overleftrightarrow. However,
	we represent it in the DOM for MathJax--it needs to get the
	grouping around the text. This corresponds to a custom macro in
	the default-layout.html AoPS template. """
	args = '{text}'

	def invoke( self, tex ):
		return super(rlin,self).invoke( tex )

# Attributions
class source(Base.Command):
	args = '{source:str}'


class MathCounts(source):
	args = ''

	def invoke(self, tex):
		res = super(MathCounts, self).invoke(tex)
		self.attributes['source'] = 'MATHCOUNTS'
		return res

class MOEMS(source):
	args = ''

	def invoke(self, tex):
		res = super(MOEMS, self).invoke(tex)
		self.attributes['source'] = 'MOEMS'
		return res

class AMC(source):
	args = '{text:str}'

	def invoke(self, tex):
		res = super(AMC, self).invoke(tex)
		self.attributes['source'] = 'AMC %s' % self.attributes['text']
		return res

# Counters

class partnumname(Base.Command):
	unicode = ''

class parts(Base.List):

	counters = ['partnum']
	args = '[ init:int ]'

	class part(plastexids.StableIDMixin,Base.List.item):
		args = ' [title] '
		# Ordinary list items can accept a value, this may or may not be used in AoPS code
		# args = ''
		counter = 'partnum'

		def invoke( self, tex ):
			# ignore the list implementation this also increments the counter.
			_t = Base.Command.invoke(self,tex)

			# Prevet the rendering of instances of \part[]
			self.alpha = None
			self.title = None
			if ( self.attributes['title'] is not None ):
				if ( self.attributes['title'].source != '' ):
					self.title = self.attributes['title']

				#self.ownerDocument.context.counters[self.counter].value = self.ownerDocument.context.counters[self.counter].value - 1
				self.ownerDocument.context.counters[self.counter].value -= 1
			else:
				self.position = self.ownerDocument.context.counters[self.counter].value
				self.alpha = "(" + _number_to_lower_alpha_list( self.position ) + ")"

			self.attributes['probnum'] = \
			    str(self.ownerDocument.context.counters['chapter'].value) + '.'+ \
			    str(self.ownerDocument.context.counters['probnum'].value)

			if (self.alpha is not None):
				self.attributes['probnum'] = self.attributes['probnum'] + "." + self.alpha

			return _t

		def digest(self, tokens):
			super(parts.part, self).digest(tokens)
			# Remove trailing commas that we have in some parts
			removeCommasFromSectionWithHints(self)

	class parthard(part):
		pass

	def invoke( self, tex ):
		_ = super(parts, self).invoke( tex ) # Notice we're not returning (TODO: why?)

		if 'init' in self.attributes and self.attributes['init']:
			self.ownerDocument.context.counters['partnum'].setcounter( self.attributes['init'] )
		elif self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['partnum'].setcounter(0)

	def digest( self, tokens ):
		#After digesting loop back over the children moving nodes before
		#the first item into the first item
		res = super(parts, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:
			nodesToMove = []

			for node in self:

				if isinstance(node, Base.List.item):
					nodesToMove.reverse()
					for nodeToMove in nodesToMove:
						self.removeChild(nodeToMove)
						node.insert(0, nodeToMove)
					break

				nodesToMove.append(node)

		return res

def removeCommasFromSectionWithHints(subsection):
	hintName = 'hint'
	for node in subsection.childNodes:
		for child in node.childNodes:
			if child.nextSibling != None and child.nextSibling.nextSibling != None:
				if 		child.nodeName == hintName \
					and child.nextSibling == ', '  \
					and child.nextSibling.nextSibling.nodeName == hintName:
					node.removeChild(child.nextSibling)
				elif	child.nodeName == hintName and child.nextSibling == ',' \
					and child.nextSibling.nextSibling.source == '~ ' \
					and child.nextSibling.nextSibling.nextSibling != None \
					and child.nextSibling.nextSibling.nextSibling.nodeName == hintName:
					node.removeChild(child.nextSibling)

def _number_to_lower_alpha_list(index):
	if index:
		return _number_to_lower_alpha_list( (index - 1) // 26 ) + chr( (index - 1) % 26 + 97 )
	return ''

# Exercises exist at the end of a section and are started with \exercises.  There is
# no explicit stop.	Exercises end when a new section starts
class exnumber(Base.Command):
	unicode = ''

class exercises(Base.subsection):
	args = ''
	counter = ''
	title = 'exercises'

	#this is used to emulate a list.  Like parts we need to make sure
	#that the first child in the list is  an exer or exerhard
	def digest( self, tokens ):
		#After digesting loop back over the children moving nodes before
		#the first item into the first item
		res = super(exercises, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:

			nodesToMove = []

			for node in self:

				if isinstance(node, exer):
					nodesToMove.reverse()
					for nodeToMove in nodesToMove:
						self.removeChild(nodeToMove)
						node.insert(0, nodeToMove)
					break

				nodesToMove.append(node)

		return res

class exer(plastexids.StableIDMixin, Base.subsubsection):
	args = ''
	counter = 'exnumber'
	title = 'exer'
	blockType = True

	def invoke( self, tex ):
		res = super(exer,self).invoke( tex )
		self.attributes['exnumber'] = 	str(self.ownerDocument.context.counters['chapter'].value) \
									  + '.' + str(self.ownerDocument.context.counters['section'].value) \
									  + '.' + str(self.ownerDocument.context.counters['exnumber'].value)

		return res

	def digest(self, tokens):
		super(exer, self).digest( tokens )
		removeCommasFromSectionWithHints(self)

	def postParse(self, tex):
		super(exer, self).postParse(tex)
		# Because we are a subsubsection our deep section level causes the ref
		# attribute to not be set in the super.	In a section with a lower sec number
		# (I.E. subsection, section, chapter...) the super would also set a captionName attribute
		self.ref = self.ownerDocument.createElement('the'+self.counter).expand(tex)
		self.captionName = self.ownerDocument.createElement(self.counter+'name').expand(tex)

class dfrac(Base.Command):
	args = 'num den'

class exerhard(exer):
	pass

class bogus(Base.Environment):
	blockType = True

class importantdef(Base.Environment):
	blockType = True

class important(Base.Environment):
	blockType = True

class concept(Base.Environment):
	blockType = True

class warning(Base.Environment):
	blockType = True

class game(Base.Environment):
	blockType = True

class sidebar(Base.Environment):
	blockType = True

class xtra(Base.Environment):
	blockType = True

titlepattern = re.compile(r'/Title\s+\((?P<title>.*?)\)\s+/Author\s+\((?P<authors>.*?)\).*')

class pdfinfo(Base.Command):
	args = 'info:str'

	#we want to do something intelligent with the argument to pdfinfo
	#For now we set the title of the document, but we may also want
	#to do something intelligent with the author
	def invoke(self, tex):
		_ = super(pdfinfo, self).invoke( tex )

		if 'info' in self.attributes:
			match = titlepattern.match(self.attributes['info'])
			title = match.group('title')
			authors = match.group('authors')

			# Prefer to accept the values created by the \title and \author
			# commands over what is in pdfinfo
			if 'title' not in self.ownerDocument.userdata:
				self.ownerDocument.userdata['title'] = title
			if 'authors' not in self.ownerDocument.userdata:
				self.ownerDocument.userdata['authors'] = authors

		return [] # But don't put anything in the dom, it doesn't render



class probref(Command):
	args = 'label:idref'

class _BasePicProblem(Base.Environment):
	args = 'pic'
	counter = 'probnum'
	blockType = True

	def invoke(self,tex):
		res = super(_BasePicProblem,self).invoke( tex )

		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									 +	'.' \
									 + str(self.ownerDocument.context.counters['probnum'].value)

		#if self.macroMode != Base.Environment.MODE_END:
		#	self.refstepcounter(tex)
		# Move from the argument into the DOM
		if 'pic' in self.attributes:
			self.appendChild( self.attributes['pic'] )
		return res

class picproblem(_BasePicProblem):
	pass

class picsecprob(_BasePicProblem):
	pass


class problem(Base.Environment):
	args = '[unknown]'
	counter = 'probnum'
	blockType = True

	def invoke( self, tex ):
		# if self.macroMode != Base.Environment.MODE_END:
		#	self.refstepcounter(tex)
		res = super(problem,self).invoke( tex )
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

class problemspec(problem):
	pass

def _digestAndCollect( self, tokens, until ):
	self.digestUntil(tokens, until )
	# Force grouping into paragraphs to eliminate the empties
	if getattr(self, 'forcePars', True):
		self.paragraphs()

class sectionproblems(Base.subsection):
	counter = 'sectionprobsnotused'
	args = ''
	title = 'sectionproblems'

	def invoke( self, tex ):
		self.ownerDocument.context.counters['saveprobnum'].setcounter(self.ownerDocument.context.counters['probnum'] )
		return super(sectionproblems,self).invoke( tex )

	def digest(self, tokens):
		_digestAndCollect( self, tokens, nomoresectionproblems )

		#Adapted from Environment.paragraphs
		for i in range(len(self)-1, -1, -1):
			item = self[i]
			# Filter out any empty paragraphs
			if item.level == Node.PAR_LEVEL:
				if len(item) == 0:
					self.pop(i)
				elif len(item) == 1 and item[0].isElementContentWhitespace:
					self.pop(i)

			#Filter out any whitespace text nodes
			elif item.nodeType == Node.TEXT_NODE:
				if item.isElementContentWhitespace:
					self.pop(i)

		#For some reason we can't combine this with the loop above previousSibling isn't correct
		for i in range(len(self)-1, -1, -1):
			item = self[i]

			if not ( isinstance(item, problem) or isinstance(item, _BasePicProblem) ):
				before = item.previousSibling
				if before is not None:
					self.pop(i)
					before.append(item)

class picsecprobspec(_BasePicProblem):
	pass

class picproblemspec(_BasePicProblem):
	pass

class secprob(problem):
	pass

class nomoresectionproblems( Base.Command ):

	blockType = True

	def invoke( self, tex ):
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )
		return super(nomoresectionproblems,self).invoke(tex)

class beginsol( Base.subsection ):
	args = ''
	counter = ''

	def invoke( self, tex ):
		res = super(beginsol, self).invoke(tex)

		#We encounter solutions right after the problem therefore our
		#solutions probnum should be the current value of the probnum counter
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

	def digest( self, tokens ):
		_digestAndCollect( self, tokens, stopsol )

class stopsol( Base.Command ):
	pass

class solution( Base.Environment ):
	args = ''
	blockType = True
	forcePars = True

	def invoke( self, tex ):
		res = super(solution, self).invoke(tex)

		#We encounter solutions right after the problem therefore our
		#solutions probnum should be the current value of the probnum counter
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

# FIXME: The use of section types for individual problems and exercises
# is probably not right. This causes them to appear in the table of contents,
# partially, but they don't have real titles. It also causes them to get NTIIDs,
# which may or may not be right.

# FIXME: These counters are not right?
# If we don't override the args attribute, these consume one letter of text
class reviewprobs(Base.section):
	args = ''
	#counter = 'probnum'
	title = 'reviewprobs'

	def invoke(self, tex):
		#pdb.set_trace();
		#Attach a title to this "section"
		docFragment = self.ownerDocument.createDocumentFragment()
		docFragment.appendText(["Review Problems"])
		self.title = docFragment

		#Save the probnum counter b/c it gets reset in the super
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )

		res = super(reviewprobs, self).invoke(tex)

		#Restore the probnum counter
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )

		return res

class challengeprobs(Base.section):
	args = ''
	#counter = 'probnum'
	title = 'challengeprobs'

	def invoke(self, tex):
		#pdb.set_trace()
		docFragment = self.ownerDocument.createDocumentFragment()
		docFragment.appendText(["Challenge Problems"])
		self.title = docFragment

		#Save the probnum counter b/c it gets reset in the super
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )

		res = super(challengeprobs, self).invoke(tex)

		#Restore the probnum counter
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )

		return res

class revprob(Base.subsection):
	args = ''
	counter = 'probnum'
	title = 'revprob'

	def invoke( self, tex ):
		res = super(revprob,self).invoke( tex )
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

	def digest(self, tokens):
		super(revprob, self).digest( tokens )
		removeCommasFromSectionWithHints( self )

class chall(Base.subsection):
	args = ''
	counter = 'probnum'
	title = 'chall'

	def invoke( self, tex ):
		res = super(chall,self).invoke( tex )
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

	def digest(self, tokens):
		super(chall, self).digest( tokens )
		removeCommasFromSectionWithHints( self )

class challhard(Base.subsection):
	args = ''
	counter = 'probnum'
	title = 'challhard'

	def invoke( self, tex ):
		res = super(challhard,self).invoke( tex )
		self.attributes['probnum'] =	str(self.ownerDocument.context.counters['chapter'].value) \
									+	'.' \
									+	str(self.ownerDocument.context.counters['probnum'].value)
		return res

	def digest(self, tokens):
		super(challhard, self).digest( tokens )
		removeCommasFromSectionWithHints( self )

# for \nth, \nst, \nrd, etc..
class nsuperscript(Base.Command):
	args = 'text'

	# We need to store if we are inside math mode
	# def invoke(self, tex):
	# 	result = super(nsuperscript, self).invoke( tex )
	# 	self.insideMathElement = self.ownerDocument.context.isMathMode
	# 	return result

	# We want to be treated as math for resource generation and rendering
	# so our source needs to make us look like a math element.  if we are
	# contained in a math element we get that for free.	If not we have to put
	# ourselves in math mode using $$
	# @property
	# def source(self):
	#	mySource = super(nsuperscript, self).source

	# 	if not self.insideMathElement:
	# 		# If we wrap our self in math environment
	# 		# we need to make sure we don't already contain math
	# 		mySource = '$%s$' % mySource

	# 	return mySource

class nst(nsuperscript):
	pass

class nnd(nsuperscript):
	pass

class nrd(nsuperscript):
	pass

class nth(nsuperscript):
	pass

class rightpic(graphicx.includegraphics):
	" For our purposes, exactly the same as an includegraphics command. "
	packageName = 'aopsbook'
	blockType = True

class leftpic(rightpic):
	pass


class fig(Base.figure):
	pass

negthinspace = getattr(Base.Text, 'negthinspace')

class negthinspaceshorthand(negthinspace):
	macroName = '!'

# Hints

class hints(_Ignored):
	pass

class hint(Crossref.label):
	pass

class thehints(Base.List):
	# We keep counters but ignore them
	counters = ['hintnum']
	args = ''

	def invoke( self, tex ):
		_ = super(thehints, self).invoke( tex ) # Not returning (TODO: Why?)

		if self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['hintnum'].setcounter(0)

	def hintToreplace( self, hintItem ):
		for hint in hintItem.idref['label'].getElementsByTagName( 'hint' ):
			if hint.attributes['label'] == hintItem.attributes['label']:
				return hint

	def digest( self, tokens ):
		super(thehints,self).digest( tokens )
		# When we end the hints, go back and fixup the references and
		# move things into the dom. Remember not to iterate across
		# self and mutate self at the same time, hence the copy
		nodes = list(self.childNodes)
		for child in nodes:
			if child.idref and child.idref['label'] and \
				   type(child.idref['label']).__module__ == 'aopsbook':
				# we are the current parent, the label needs to be the
				# new parent
				self.removeChild( child )
				replaceHint = self.hintToreplace( child )
				# How is possible that we sometimes get a hintitem with no corresponding hint?
				if replaceHint != None:
					replaceHint.parentNode.replaceChild( child, replaceHint )
					# SAJ: child sometimes contains par elements. If they are not removed, invalid
					# markup is produced. The child elements can contain the par elements because
					# we model them in a list environment and items in a list environment can
					# contain block elements. However when we perform the replacement above, we
					# are taking the node and placing it inside of an element that will be modeled
					# as an HTML5 p element, which cannot contain block, or in HTML5 speak 'flow',
					# elements.
					#
					# Since we never print the hints as a list or otherwise use them in a list
					# fashion, we should look at changing how we model the hints.
					for node in child.getElementsByTagName('par'):
						child.removeChild( node )
			else:
				# for now, if it doesn't refer to anything, delete it
				self.removeChild( child )


class hintitem(Crossref.ref):
	args = 'label:idref'

	def invoke( self, tex ):
		# self.counter = 'hintnum'
		# self.position = self.ownerDocument.context.counters[self.counter].value + 1
		# ignore the list implementation
		return Base.Command.invoke(self,tex)

	def digest(self, tokens):
		_digestAndCollect( self, tokens, hintitem )

class ntirequires(Base.Command):
	args = 'rels:dict'

	def toXML(self, *args, **kwargs):
		"""
		<nti:topic rdf:about='...'>
		  <nti:requires><aops:concept>...</aops:concept></nti:requires>
		"""
		rels = self.attributes['rels']
		xml = "<nti:topic rdf:about='" + self.findContainer() + "'>"
		for key in rels:
			xml += "<nti:requires><aops:concept>" + key + "<aops:concept><nti:requires>"
		xml += "</nti:topic>"
		return xml

	def findContainer(self):
		# parent node should have the 'title' attribute
		result = ""
		parentNode = self.parentNode
		while parentNode:
			if hasattr(parentNode.attributes,'title'):
				result = parentNode.attributes['title']
				break
			parentNode = parentNode.parentNode
		return result

# AoPS Custom Math Operators

class lcm(Command):
	args = ''

# AoPS 'Hacks'

class davesuglyhack(Command):
	args = ''

# Indexes in math equations turn out to mess up
# mathjax rendering. Thus we remove them.

class index(Index.index):

	def invoke(self, tex):
		result = super(index,self).invoke( tex )
		if self.ownerDocument.context.isMathMode:
			self.ownerDocument.userdata['index'].pop()
			result = []
		return result

def ProcessOptions( options, document ):
	document.context.newcounter( 'exnumber' , resetby='section')
	document.context.newcounter( 'partnum' )

	# used in \begin{problem}.
	# TODO: Get this to reset in chapters (probably not important)
	document.context.newcounter( 'probnum' , resetby='chapter')

	# With customising the paths, we could use absolotue paths and fix
	# the temporary directory issue? Really only important for direct
	# HTML rendering
	document.userdata.setPath( 'packages/aopsbook/paths', ['.', '../Images/'])
	document.userdata.setPath( 'packages/graphicx/paths', ['.', '../Images/'])

	# AoPS uses fully qualified image names, so we don't want to
	# search for multiple extensions; that really slows things down
	# since it spawns an external program (1 mi nvs 20 secs)
	document.userdata.setPath( 'packages/graphicx/extensions',
							   [] )
	document.userdata.setPath( 'packages/aopsbook/extensions', [])

	# hints
	document.context.newcounter( 'hintnum' )

	document.context.newcounter('sectionprobsnotused')
	document.context.newcounter('challprobsnotused')
	document.context.newcounter('reviewprobsnotused')
