from plasTeX import Base, Node
import plasTeX
import traceback


def transform(document):
	# Chapterauthor and chapterquote need to move down a level, inside
	# their respective chapters. NOTE: They use the same
	# macros for the book quote, the first one, which we want to leave alone.
	for chapterquote in document.getElementsByTagName( 'chapterquote')[1:]:
		chapterauthor = chapterquote.parentNode.getElementsByTagName( 'chapterauthor' )[0]
		parent = chapterquote.parentNode
		# move it up out of containing par and raggedbottom, etc
		while parent:
			if parent.nextSibling and parent.nextSibling.nodeName == 'chapter':
				break
			parent = parent.parentNode

		if parent and parent.nextSibling:
			chapterquote.parentNode.removeChild( chapterauthor )
			chapterquote.parentNode.removeChild( chapterquote )
			parent.nextSibling.insert( 0, chapterquote )
			parent.nextSibling.insert( 1, chapterauthor )
			traceback.print_exc()