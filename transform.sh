#!/bin/bash

MYPATH=`dirname $0`
export XHTMLTEMPLATES=$MYPATH/../renderers
export PYTHONPATH=$MYPATH:$MYPATH/../plastex/:$PYTHONPATH


${PYTHON:-python2.7} $MYPATH/aopstoxml $1 $2

