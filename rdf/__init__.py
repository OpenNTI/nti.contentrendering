from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.term import URIRef, Literal, BNode
from rdflib.namespace import Namespace, RDF, RDFS

store = ConjunctiveGraph()

# Bind a few prefix, namespace pairs.
store.bind("dc", "http://http://purl.org/dc/elements/1.1/")
store.bind("foaf", "http://xmlns.com/foaf/0.1/")
store.bind( "nti", "http://nextthought.com/xml/v1/" )
store.bind( "aops", "http://nextthought.com/xml/v1/aops/prealgebra/" )

DC = Namespace(  "http://http://purl.org/dc/elements/1.1/" )
NTI = Namespace( "http://nextthought.com/xml/v1/" )
AOPS = Namespace( "http://nextthought.com/xml/v1/aops/prealgebra/" )
#FOAF = Namespace( "http://xmlns.com/foaf/0.1/" )

chapter = None
chapterName = None
section = None

def parseRequires( macroName, chapter, section ):
	name = line[len( macroName + '{'):-1]
	addTo = None
	if section: addTo = section
	elif chapter: addTo = chapter
	else: return AOPS[name]


	store.add( (addTo, NTI[macroName[1:].title()], AOPS[name]) )
	store.add( (AOPS[name], RDFS.label, Literal(name)))
	return AOPS[name]

def parseNode( macroName ):
	name = line[len( macroName + '{'):-1]
	chapter = AOPS[name]
	store.add( (chapter, RDF.type, NTI[macroName[1:].title()]) )
	store.add( (chapter, DC["Title"], Literal(name)) )
	store.add( (chapter, RDFS.label, Literal(name)) )
	return (chapter,name)

with open( "PrealgebraMetadata.txt" ) as f:
	for line in f:
		line = line.strip()
		if line.startswith( "#" ):
			continue
		if line.startswith( "\chapter" ):
			chapter,chapterName = parseNode( '\chapter' )
			section = None
			holdForSection = []
		elif line.startswith( "\section" ):
			section,name = parseNode( '\section' )
			store.add( (section, NTI['sectionOf'], chapter))
			for requires in holdForSection:
				store.add( (section, NTI['Require'], requires) )
			#holdForSection = []
		elif line.startswith( "\\require" ):
			requires = parseRequires( "\\require", chapter, section )
			if not section:
				holdForSection.append( requires )
		elif line.startswith( "\provide"):
			value = parseRequires( "\provide", chapter, section )
			if chapter:
				store.add( (chapter, NTI['Provide'], value ) )

print store.serialize(format="pretty-xml")

#s = NTI['Require']
#v = AOPS['integer.arithmetic']

#for i in store.transitive_subjects( s, v ):
#	print i
