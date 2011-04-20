#!/usr/bin/env PYTHONPATH=/Users/jmadden/Projects/AoPS/src/main/ /opt/local/bin/python2.7

import os
from mathtex.mathtex_main import Mathtex

import cgitb
cgitb.enable()

print 'Content-Type: image/svg+xml'
print
import sys
sys.stdout.flush()
import cgi
#cgi.print_environ()

form = cgi.FieldStorage()

m = Mathtex( form.getfirst('tex') )
m.save('/dev/stdout', 'svg')
