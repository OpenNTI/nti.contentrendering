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


class Def(_OneText):
	pass

class Defnoindex(_OneText):
	pass

class angle(Base.Command):

	def invoke( self, tex ):
		super(angle, self).invoke(  tex )

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

class picsecprob(Base.Environment):
	args = ' pic '

	def invoke( self, tex ):
		if self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['probnum'].stepcounter()
		return super(picsecprob,self).invoke( tex )


class sectionproblems(Base.subsection):
	counter = 'probnum'

	def invoke( self, tex ):
		self.ownerDocument.context.counters['saveprobnum'].setcounter(
			self.ownerDocument.context.counters['probnum'] )
		return super(sectionproblems,self).invoke( tex )

	def digest(self, tokens):
		"""
		Items should absorb all of the content within that
		item, not just the `[...]' argument.  This is
		more useful for the resulting document object.

		"""
		for tok in tokens:
			if tok.isElementContentWhitespace:
				continue
			tokens.push(tok)
			break
		self.digestUntil(tokens, nomoresectionproblems)
		# Force grouping into paragraphs to eliminate the empties
		self.paragraphs()

class picsecprobspec(picsecprob):
	pass

class secprob(picsecprob):
	args = ''


class nomoresectionproblems( Base.Command ):

	blockType = True

	def invoke( self, tex ):
		self.ownerDocument.context.counters['probnum'].setcounter(
			self.ownerDocument.context.counters['saveprobnum'] )
		return super(nomoresectionproblems,self).invoke(tex)


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
#	packageName = 'aopsbook'


	def invoke( self, tex ):
		# literally replace it with include graphics. This doesn't seem to be quite working at
		# render time.
		node = includegraphics()
		node.parentNode = self.parentNode
		node.ownerDocument = self.ownerDocument
		res = node.invoke( tex )
		if res is None:
			self._backup = node
			# FIXME: Returning this as a list (to completely replace this object) doesn't work.
			# Do we understand that wrong?
			return node
		return res

	def __getattribute__(self, value ):
		# TODO: With replacement working, this is useless
		if value == 'imageoverride':
			return getattr( self._backup, value )
		return includegraphics.__getattribute__( self, value )


leftpic = rightpic
parpic = rightpic

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

	document.userdata.setPath( 'packages/graphicx/extensions',
							   ['.pdf', '.png','.jpg','.jpeg','.gif','.ps','.eps'])


