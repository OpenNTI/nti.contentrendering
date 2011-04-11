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
		print 'Invoking parts'
		res = super(parts, self).invoke( tex )
		print self.attributes
		if 'init' in self.attributes and self.attributes['init']:
			self.ownerDocument.context.counters['partnum'].setcounter( self.attributes['init'] )
		elif self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters['partnum'].setcounter(0)

	pass

class part(Base.List.item):
#	args = ''

	def invoke( self, tex ):
		self.counter = 'partnum'
		self.position = self.ownerDocument.context.counters[self.counter].value + 1
		print 'Part position %s' % self.position
		#ignore the list implementation
		return Command.invoke(self,tex)


	def digest( self, tex ):
		super( part, self ).digest( tex )

class bogus(Base.Environment):
	pass


from plasTeX.Packages.graphicx import *

#class includegraphics(_OneText):
#	pass

def ProcessOptions( options, document ):
	document.context.newcounter( 'partnum' )


