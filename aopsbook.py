from plasTeX import Base

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




class rule(Base.Boxes.rule):
	" Rules have no place in this DOM"
	def invoke( self, tex ):
		super(rule,self).invoke( tex )
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


class Def(_OneText):
	pass

class Defnoindex(_OneText):
	pass

class angle(Base.Command):

	def invoke( self, tex ):
		super(angle, self).invoke(  tex )

# Citations
class MathCounts(_Ignored):
	#TODO: How to represent this?
	pass

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
	counter = ''

class exer(Base.subsubsection):
	args = ''
	counter='exnumber'

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



from plasTeX.Base import Crossref

class probref(Crossref.ref):
	pass

class _BasePicProblem(Base.Environment):
	args = 'pic'

	def invoke(self,tex):
		res = super(_BasePicProblem,self).invoke( tex )
		if self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['probnum'].stepcounter()
		# Move from the argument into the DOM
		if 'pic' in self.attributes:
			self.appendChild( self.attributes['pic'] )
		return res

class picproblem(_BasePicProblem):
	pass

class picsecprob(_BasePicProblem):
	pass

class problem(Base.Environment):
	args = ' [unknown] '

	def invoke( self, tex ):
		if self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['probnum'].stepcounter()
		super(problem,self).invoke( tex )
		self.attributes['probnum'] = self.ownerDocument.context.counters['probnum'].value

def _digestAndCollect( self, tokens, until ):
	for tok in tokens:
		if tok.isElementContentWhitespace:
			continue
		tokens.push(tok)
		break
	self.digestUntil(tokens, until )
	# Force grouping into paragraphs to eliminate the empties
	self.paragraphs()

class sectionproblems(Base.subsection):
	counter = 'probnum'

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
	args = ''

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
	counter = 'probnum'

class challengeprobs(Base.section):
	args = ''
	counter = 'probnum'

class revprob(Base.subsection):
	args = ''

class chall(Base.subsection):
	args = ''

class challhard(Base.subsection):
	args = ''


from plasTeX.Packages.graphicx import *

class rightpic(includegraphics):
	" For our purposes, exactly the same as an includegraphics commend. "
	packageName = 'aopsbook'

class leftpic(rightpic):
	pass
class parpic(rightpic):
	pass


class fig(Base.figure):
	pass

## Hints
class hints(_Ignored):
	pass

class hint(Crossref.label):

	def invoke( self, tex ):
		res = super( hint, self ).invoke( tex )
		return res


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


def ProcessOptions( options, document ):

	document.context.newcounter( 'exnumber' )

	document.context.newcounter( 'partnum' )

	# used in \begin{problem}.
	# TODO: Get this to reset in chapters (probably not important)
	document.context.newcounter( 'probnum' )

	# With customising the paths, we could use absolotue paths and fix
	# the temporary directory issue? Really only important for direct
	# HTML rendering
	document.userdata.setPath( 'packages/aopsbook/paths', ['.', '../Images/'])
	document.userdata.setPath( 'packages/graphicx/paths', ['.', '../Images/'])

#	document.userdata.setPath( 'packages/graphicx/extensions',
#							   ['.pdf', '.png','.jpg','.jpeg','.gif','.ps','.eps'])

	# hints
	document.context.newcounter( 'hintnum' )


