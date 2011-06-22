from plasTeX import Base

class _Ignored(Base.Command):
	unicode = ''
	def invoke( self, tex ):
		return []

class problem(Base.Environment):
	pass
	
class question(Base.Environment):
	pass

class solution(Base.Environment):
	pass

class tab(Base.Command):
	pass

class includegraphics(Base.Command):
	pass

def ProcessOptions( options, document ):
	document.context.newcounter( 'probnum')
	document.context.newcounter( 'solnum' )



