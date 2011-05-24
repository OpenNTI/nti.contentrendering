from rdflib.graph import Graph
from rdflib.term import URIRef, Literal, BNode
from rdflib.namespace import Namespace, RDF

store = Graph()

# Bind a few prefix, namespace pairs.
store.bind("dc", "http://http://purl.org/dc/elements/1.1/")
store.bind("foaf", "http://xmlns.com/foaf/0.1/")
store.bind( "nti", "http://nextthought.com/xml/v1/" )
store.bind( "aops", "http://nextthought.com/xml/v1/aops/prealgebra/" )

DC = Namespace(  "http://http://purl.org/dc/elements/1.1/" )
NTI = Namespace( "http://nextthought.com/xml/v1/" )
AOPS = Namespace( "http://nextthought.com/xml/v1/aops/prealgebra/" )

# Create an identifier to use as the subject for Donna.
donna = BNode()

# Add triples using store's add method.
#store.add((donna, RDF.type, FOAF["Person"]))
#store.add((donna, FOAF["nick"], Literal("donna", lang="foo")))
#store.add((donna, FOAF["name"], Literal("Donna Fales")))

chapter = None
chapterName = None
section = None

def parseRequires( macroName, chapter, section ):
	addTo = None
	if section: addTo = section
	else: addTo = chapter

	name = line[len( macroName + '{'):-1]
	store.add( (addTo, NTI[macroName[1:].title()], AOPS[name]) )
	return AOPS[name]

def parseNode( macroName ):
#	chapter = BNode()
	name = line[len( macroName + '{'):-1]
	chapter = AOPS[name]
#	store.add( (chapter, RDF.ID, AOPS[name] ) )
	store.add( (chapter, RDF.type, NTI[macroName[1:].title()]) )
	store.add( (chapter, DC["Title"], Literal(name)) )
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
			holdForSection = []
		elif line.startswith( "\require" ):
			requires = parseRequires( "\require", chapter, section )
			if not section:				holdForSection.append( requires )
		elif line.startswith( "\provide"):
			value = parseRequires( "\provide", chapter, section )
			if chapter:
				store.add( (chapter, NTI['Provide'], value ) )

print store.serialize(format="pretty-xml")
