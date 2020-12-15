#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os,sys,subprocess
from codescanner_analysis import CodescannerAnalysisData as CAD

RESULTFOLDER = "/ram/"

# Example code

# Description:
# Quickly plots a binary, with byteplot and colormap, to RESULTDIR.
# 
# python2 quick_codescan.py binary 
# or
# python2 quick_codescan.py binary (0xstart) (0xend) (a=1 for aggressive mode)

# Notes:
# * The imports assume codescanner_analysis is globally installed (or use virtualenv).
#   Or change the imports to your liking.

# * This probably works only with python2 and needs to be adapted for python3.


if __name__=="__main__":
    
    if (len(sys.argv) < 2):
        print("Usage: python2 quick_codescan.py binary (0xstart) (0xend) (a=1 for aggressive mode)")
        sys.exit()
        
    finamepath = str(sys.argv[1])
    
    if not os.path.isfile(finamepath):
        print("File not found: '%s'" % (finamepath))
        sys.exit()
    
    finamesize = os.path.getsize(finamepath)
    aggressive = 0
    
    cad = None
    if (len(sys.argv) > 2):
        if (len(sys.argv[2]) ==3 ):
            if ("a=1" == sys.argv[2]): # a bit ugly but safe.
                aggressive = 1
                print("Using aggressive mode!")
                cad = CAD(finamepath,0,finamesize,aggressive)
        else:
            startAt = int(sys.argv[2],base=16)
            endsAt = int(sys.argv[3],base=16)
            cad = CAD(finamepath,startAt,endsAt)
    else:
        cad = CAD(finamepath)
        
    if cad is None:
        print("error: cad object is None!")
        sys.exit()
        
    print(cad.decision)
    print(cad.file_header)
    print(cad.architecture)
    
    short_finame = os.path.split(finamepath)[1]
    
    finame_template = ""
    fi_splitext = os.path.splitext(short_finame)
    if (fi_splitext[1]):
        finame_template = "%s_%s" % (fi_splitext[0],fi_splitext[1][1:])  # dot-extension
    else:
        finame_template = fi_splitext[0] # Elf-Binaries without dot-extension
    
    pngname1 = "%s_byteplot.png" % (finame_template)
    pngname2 = "%s_colormap.png" % (finame_template)
        
    cad.plot_to_file(os.path.join(RESULTFOLDER,pngname1), 150, 1)
    cad.plot_to_file(os.path.join(RESULTFOLDER,pngname2), 150, 2)
    
    sys.exit()
