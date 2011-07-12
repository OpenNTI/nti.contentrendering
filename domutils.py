from plasTeX import Base

def findNodes(node, nodeName):
	nodes=[]
	#print 'looking at node %s'%node
	if getattr(node, 'nodeName', '') == nodeName:
		nodes.append(node)

	if getattr(node, 'attributes', None):
		for attrval in node.attributes.values():
			if getattr(attrval, 'childNodes', None):
				for child in attrval.childNodes:
					nodes.extend(findNodes(child, nodeName))

	if node.childNodes:
		for child in node.childNodes:
			nodes.extend(findNodes(child, nodeName))

	return list(set(nodes))

def findNodesStartsWith(node, startsWith):
	nodes=[]
	#print 'looking at node %s'%node
	if getattr(node, 'nodeName', '').startswith(startsWith):
		nodes.append(node)

	if getattr(node, 'attributes', None):
		for attrval in node.attributes.values():
			if getattr(attrval, 'childNodes', None):
				for child in attrval.childNodes:
					nodes.extend(findNodesStartsWith(child, startsWith))

	if node.childNodes:
		for child in node.childNodes:
			nodes.extend(findNodesStartsWith(child, startsWith))

	return list(set(nodes))
