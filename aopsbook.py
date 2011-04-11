from plasTeX import Base

class _OneText(Base.Command):
	args = 'text:str'

	def invoke( self, tex ):
		self.parse( tex )
		print self.__dict__

class Def(_OneText):
	pass

class Defnoindex(_OneText):
	pass

class angle(Base.Command):

	def invoke( self, tex ):
		super(angle, self).invoke(  tex )

class parts(Base.List):
	pass

class part(Base.List.item):
	pass


from plasTeX.Packages.graphicx import *

#class includegraphics(_OneText):
#	pass


