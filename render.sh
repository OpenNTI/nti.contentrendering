#!/bin/bash

MYPATH=`dirname $0`
export XHTMLTEMPLATES=$MYPATH/../renderers
export PYTHONPATH=$MYPATH:$MYPATH/../plastex/

python2.7 ~/bin/plastex/plasTeX/plastex --xml --save-image-file --split-level=0 --image-compiler=pdflatex --imager=gspdfpng2 --disable-image-cache --vector-imager=pdf2svg $1

