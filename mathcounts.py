from plasTeX import Base

class _Ignored(Base.Command):
	unicode = ''
	def invoke( self, tex ):
		return []

class problem(Base.Environment):
	counter = 'probnum'
	def invoke( self, tex ):
		res = super(problem,self).invoke( tex )		
		self.stepcounter(self.counter)
		self.attributes[self.counter] = self.ownerDocument.context.counters[self.counter].value
		self.ownerDocument.context.counters['solnum'].setcounter(0)
		return res
	
class question(Base.Environment):
	pass

class solution(Base.Environment):
	counter = 'solnum'
	def invoke( self, tex ):
		res = super(problem,self).invoke( tex )
		self.stepcounter(self.counter)
		self.attributes[self.counter] = self.ownerDocument.context.counters[self.counter].value
		return res

def ProcessOptions( options, document ):
	document.context.newcounter( 'probnum')
	document.context.newcounter( 'solnum' , resetby='problem')



