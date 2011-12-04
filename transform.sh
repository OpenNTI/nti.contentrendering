#!/bin/bash

MYPATH=`dirname $0`
ROOT=$MYPATH/../../..
export XHTMLTEMPLATES=$ROOT/renderers
export PYTHONPATH=$MYPATH:$ROOT/python-libs/:$PYTHONPATH


${PYTHON:-python2.7} $MYPATH/aopstoxml $1 $2

