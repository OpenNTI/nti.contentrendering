#!/bin/bash

MYPATH=`dirname $0`
export XHTMLTEMPLATES=$MYPATH/../renderers
export PYTHONPATH=$MYPATH:$HOME/bin/plastex

python2.7 ~/bin/plastex/plasTeX/plastex --xml --save-image-file --image-compiler=pdflatex --imager=gspdfpng --enable-image-cache --vector-imager=pdf2svg $1

