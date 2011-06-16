from plasTeX import Base
import re


class _OneText(Base.Command):
	args = 'text:str'

	def invoke( self, tex ):
		return super(_OneText, self).invoke( tex )

class _Ignored(Base.Command):
	unicode = ''
	def invoke( self, tex ):
		return []

#
# Presentation things to ignore
#

class rindent(_Ignored):
	pass

class vupnud(_Ignored):
	pass

class picskip(Base.Command):
	args = ' {text:int} '

	def invoke( self, tex ):
		# There's a {0} or so with this that we need to discard too
		# TODO: This may not be the best way
		tex.readGrouping( '{}' )
		return []

	def digest( self, tokens ):
		return super(picskip,self).digest( tokens )

## class newline(Base.Command):
## 	macroName = '\\'

## 	def toXML(self):
## 		return '<newline/>'

def digestUntilNextTextSize(self, tokens):
	return _digestAndCollect( self, tokens, Base.FontSelection.TextSizeDeclaration )

Base.FontSelection.TextSizeDeclaration.digest=digestUntilNextTextSize



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

	def invoke( self, tex ):
		#TODO: Can we read the next command, which should be the
		#\chapterauthor and add that as a child node?
		tokens, source = tex.readGrouping( '{}', expanded=True, parentNode=self)
		self += tokens
		return None

class chapterauthor(Base.Command):
	args = ''

	def invoke( self, tex ):
		self += tex.readGrouping( '{}', expanded=True, parentNode=self)[0]
		return None


class Def(_OneText):
	pass

class Defnoindex(_OneText):
	args = 'text'

class text(Base.BoxCommand):

	args = '{self}'

	def __init__(self):
		#pdb.set_trace()
		self.arguments[0].options['stripLeadingWhitespace']=True
		print self.arguments

	def invoke( self, tex ):
		return super(text,self).invoke( tex )

#TODO does this get handled like ^
class textsuperscript(Base.Command):
	args = 'text:str'
	pass

#We would like to be able to normalize math mode
#at parse time such that expressions like $24$ automatically
#become simple text nodes, but that's not (easily) possible: we cannot
#make that decision until after the children are parsed, and by then
#we're in the DOM (the digest() method does not yet have the proper parentNode)
#to remove

class angle(Base.Command):

	def invoke( self, tex ):
		super(angle, self).invoke(  tex )


# The rlin command and the vv command break rendering of
# vectors, so they are disabled.
# class rlin(Base.Command):
# 	""" A presentation command that means overleftrightarrow """
# 	args = ''

# 	def invoke( self, tex ):
# 		arrow = self.ownerDocument.createElement( 'overleftrightarrow' )
# 		expr = tex.readGrouping( '{}', expanded=True, parentNode=arrow)[0]
# 		arrow += expr
# 		return [arrow]

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


## rlin is re-enabled for the sake of mathjax
class rlin(Base.Command):
 	""" A presentation command that means overleftrightarrow. However,
	we represent it in the DOM for MathJax--it needs to get the
	grouping around the text. This corresponds to a custom macro in
	the default-layout.html AoPS template. """
 	args = '{text}'

 	def invoke( self, tex ):
		return super(rlin,self).invoke( tex )

# Attributions
class attribution(Base.Command):
	#No reason to have an invoke method, not doing anything special here.
	#def invoke( self, tex ):
	#	super(attribution, self).invoke( tex )

	def toXML(self):
		xml = "<nti:attribution "
		xml += "nti:type='" + self.attribution_type + "'"
		if 'value' in self.attributes and self.attributes['value']:
			xml += " nti:value='" + `self.attributes['value']` + "' ";
		xml += "/>"
		return xml

class MathCounts(attribution):
	attribution_type = "MathCounts"

class MOEMS(attribution):
	attribution_type = "MOEMS"

class AMC(attribution):
	args='{value:int}'
	attribution_type = "AMC"

# Counters
class partnum(Base.Command):
	unicode = ''

class parts(Base.List):

	counters = ['partnum']
	args = '[ init:int ]'

	def invoke( self, tex ):
		res = super(parts, self).invoke( tex )

		if 'init' in self.attributes and self.attributes['init']:
			self.ownerDocument.context.counters['partnum'].setcounter( self.attributes['init'] )
		elif self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['partnum'].setcounter(0)


class part(Base.List.item):
	#Ordinary list items can accept a value, this may or may not be used in AoPS code
	#args = ''

	def invoke( self, tex ):
		self.counter = 'partnum'
		self.position = self.ownerDocument.context.counters[self.counter].value + 1
		#ignore the list implementation
		return Command.invoke(self,tex)


	def digest( self, tex ):
		super( part, self ).digest( tex )

#Exercises exist at the end of a section and are started with \exercises.  There is
#no explicit stop.  Exercises end when a new section starts

class exnumber(Base.Command):
	unicode = ''

class exercises(Base.subsection):
	args = ''
	counter= ''

class exer(Base.subsubsection):
	args = ''
	counter='exnumber'

	def postParse(self, tex):
		super(exer, self).postParse(tex)

		#Because we are a subsubsection our deep section level causes the ref
		#attribute to not be set in the super.  In a section with a lower sec number
		#(I.E. subsection, section, chapter...) the super would also set a captionName attribute
		self.ref = self.ownerDocument.createElement('the'+self.counter).expand(tex)
		self.captionName = self.ownerDocument.createElement(self.counter+'name').expand(tex)



class exerhard(exer):
	pass

class bogus(Base.Environment):
	pass

class importantdef(Base.Environment):
	pass

class important(Base.Environment):
	pass

class concept(Base.Environment):
	pass

class warning(Base.Environment):
	pass

class game(Base.Environment):
	pass

class sidebar(Base.Environment):
	pass

titlepattern = re.compile(r'/Title\s+\((?P<title>.*?)\)\s+/Author\s+\((?P<authors>.*?)\).*')

class pdfinfo(Base.Command):
	args = 'info:str'

	#we want to do something intelligent with the argument to pdfinfo
	#For now we set the title of the document, but we may also want
	#to do something intelligent with the author
	def invoke(self, tex):
		res = super(pdfinfo, self).invoke( tex )

		if 'info' in self.attributes:
			match = titlepattern.match(self.attributes['info'])
			title = match.group('title')
			authors = match.group('authors')

			self.ownerDocument.userdata['title']=title
			self.ownerDocument.userdata['authors']=authors

		return res;

from plasTeX.Base import Crossref

class probref(Crossref.ref):
	pass

class _BasePicProblem(Base.Environment):
	args = 'pic'
	counter = 'probnum'
	def invoke(self,tex):
		res = super(_BasePicProblem,self).invoke( tex )
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

import pdb

class problem(Base.Environment):
	args = '[unknown]'
	counter = 'probnum'
	def invoke( self, tex ):
		#if self.macroMode != Base.Environment.MODE_END:
		#	self.refstepcounter(tex)


		res = super(problem,self).invoke( tex )
		self.attributes['probnum'] = self.ownerDocument.context.counters['probnum'].value
		return res



def _digestAndCollect( self, tokens, until ):
	self.digestUntil(tokens, until )
	# Force grouping into paragraphs to eliminate the empties
	self.paragraphs()

class sectionproblems(Base.subsection):
	counter = 'sectionprobsnotused'

	def invoke( self, tex ):
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )
		return super(sectionproblems,self).invoke( tex )

	def digest(self, tokens):
		_digestAndCollect( self, tokens, nomoresectionproblems )


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

	def digest( self, tokens ):
		_digestAndCollect( self, tokens, stopsol )

class stopsol( Base.Command ):
	pass

class solution( Base.Environment ):
	args = ''
	blockType = True
	forcePars = True


# FIXME: These counters are not right?
# If we don't override the args attribute, these consume one letter of text
class reviewprobs(Base.section):
	args = ''
	#counter = 'probnum'

	def invoke(self, tex):
		print 'Invoking review progs'
		#pdb.set_trace();
		#Attach a title to this "section"
		docFragment = self.ownerDocument.createDocumentFragment();
		docFragment.appendText(["Review Problems"]);
		self.title=docFragment;

		#Save the probnum counter b/c it gets reset in the super
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )

		res = super(reviewprobs, self).invoke(tex);

		#Restore the probnum counter
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )

		return res;

class challengeprobs(Base.section):
	args = ''
	#counter = 'probnum'
	def invoke(self, tex):
		print 'Invoking chall progs'
		#pdb.set_trace()
		docFragment = self.ownerDocument.createDocumentFragment();
		docFragment.appendText(["Challenge Problems"]);
		self.title=docFragment;

		#Save the probnum counter b/c it gets reset in the super
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )

		res = super(challengeprobs, self).invoke(tex);

		#Restore the probnum counter
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )

		return res;


class revprob(Base.subsection):
	args = ''
	counter = 'probnum'

	def invoke( self, tex ):
		res = super(revprob,self).invoke( tex )
		self.attributes['probnum'] = self.ownerDocument.context.counters['probnum'].value
		return res

class chall(Base.subsection):
	args = ''
	counter = 'probnum'

	def invoke( self, tex ):
		res = super(chall,self).invoke( tex )
		self.attributes['probnum'] = self.ownerDocument.context.counters['probnum'].value
		return res

class challhard(Base.subsection):
	args = ''
	counter = 'probnum'

	def invoke( self, tex ):
		res = super(challhard,self).invoke( tex )
		self.attributes['probnum'] = self.ownerDocument.context.counters['probnum'].value
		return res

from plasTeX.Base import Math

#inlineMathTypes=['svg',  'mathjax_inline']
#displayMathTypes=['svg', 'mathjax_display']

inlineMathTypes = ['mathjax_inline']
displayMathTypes = ['mathjax_display']

Math.math.resourceTypes = inlineMathTypes
#Math.ensuremath.resourceTypes=inlineMathTypes

Math.displaymath.resourceTypes = displayMathTypes
#Math.equation.resourceTypes=displayMathTypes
#Math.eqnarray.resourceTypes=displayMathTypes
#Math.EqnarrayStar.resourceTypes=displayMathTypes


#TODO this xymatrix junk is not right but it allows us to get past it for now
class xymatrix(Base.Command):
	args='text:str'

from plasTeX.Packages.fancybox import *

from plasTeX.Packages.graphicx import *

from plasTeX.Packages.amsmath import *

align.resourceTypes = displayMathTypes
AlignStar.resourceTypes = displayMathTypes
alignat.resourceTypes = displayMathTypes
AlignatStar.resourceTypes = displayMathTypes
gather.resourceTypes = displayMathTypes
GatherStar.resourceTypes = displayMathTypes

from plasTeX.Packages.multicol import *

#includegraphics.resourceTypes = ['png', 'svg']
includegraphics.resourceTypes = ['png']

class rightpic(includegraphics):
	" For our purposes, exactly the same as an includegraphics command. "
	packageName = 'aopsbook'

class leftpic(rightpic):
	pass

## Parpic takes more arguments than rightpic/includegraphics does. If we don't
## parse them, we get yick in the DOM/HTML
class parpic(includegraphics):
	args = '* [ options:dict ] file:str'


class fig(Base.figure):
	pass

## Hints
class hints(_Ignored):
	pass

class hint(Crossref.label):

	def invoke( self, tex ):
		res = super( hint, self ).invoke( tex )
		return res

class xymatrix(Base.Command):
	args='source:nox'

class thehints(Base.List):
	# We keep counters but ignore them
	counters = ['hintnum']
	args = ''

	def invoke( self, tex ):
		res = super(thehints, self).invoke( tex )

		if self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['hintnum'].setcounter(0)

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
				child.idref['label'].appendChild( child )
			else:
				# for now, if it doesn't refer to anything, delete it
				self.removeChild( child )


class hintitem(Crossref.ref):
	args = 'label:idref'

	def invoke( self, tex ):
#		self.counter = 'hintnum'
#		self.position = self.ownerDocument.context.counters[self.counter].value + 1
		#ignore the list implementation
		return Command.invoke(self,tex)

	def digest(self, tokens):
		_digestAndCollect( self, tokens, hintitem )

class ntirequires(Base.Command):
	args = 'rels:dict'

	def toXML(self):
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

from plasTeX.Base.LaTeX import Index
###
### Indexes in math equations turn out to mess up
### mathjax rendering. Thus we remove them.
class index(Index.index):

	def invoke(self, tex):
		result = super(index,self).invoke( tex )
		if self.ownerDocument.context.isMathMode:
			self.ownerDocument.userdata['index'].pop()
			result = []
			print 'Ignoring index in math!!!'
		return result

def ProcessOptions( options, document ):

	document.context.newcounter( 'exnumber' , resetby='chapter')

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
	document.context.newcounter('challprobsnotused');
	document.context.newcounter('reviewprobsnotused')



