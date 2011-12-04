#!/bin/bash

MYPATH=`dirname $0`
ROOT=$MYPATH/../../..
export XHTMLTEMPLATES=$ROOT/renderers
export PYTHONPATH=$MYPATH:$ROOT/python/:$PYTHONPATH


${PYTHON:-python2.7} -m nti.contentrendering.aopstoxml $1 $2

