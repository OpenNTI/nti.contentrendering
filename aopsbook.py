from plasTeX import Base

class _OneText(Base.Command):
	args = 'text:str'

	def invoke( self, tex ):
		return super(_OneText, self).invoke( tex )

class rindent(Base.Command):

	def invoke( self, tex ):
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

#Exercises seem similar to parts so maybe this gets duplicated.
class exercieses(Base.List):
	pass

class exer(Base.List.item):
	pass

class exerhard(Base.List.item):
	pass

class bogus(Base.Environment):
	pass

class importantdef(Base.Environment):
	pass

class important(Base.Environment):
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


