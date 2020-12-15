#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys,subprocess
from codescanner_analysis import CodescannerAnalysisData as CAD

import os,sys,inspect
import subprocess
import shutil
import re
import shutil
import time
import pickle
import errno

RESULTFOLDER = "/ram/"

# Example code

# Description:
# Take an input folder (with subdirs) and simply batch codescan all to RESULTDOLDER.

# The imports assume codescanner_analysis is globally installed (or use virtualenv).
# Or change the imports to your liking.

def dummyfunction(finamepath):
    
    print(finamepath)
    
    return


def plot_file(finamepath):
    
    print(finamepath)
    
    finamesize = os.path.getsize(finamepath)
    cad = None
    
    if (finamesize > (1024*1024*2)): 
        startAt = 0
        endsAt = (1024*1024*2)
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
    
    pngname = "%s.png" % (finame_template)
        
    cad.plot_to_file(os.path.join(RESULTFOLDER,pngname), 75,1)
    
    return 
    

def DoSomethingWithFiles(FileList):
    
    for f in FileList:
        if ("~" == f[-1]):
            fipath, finame = os.path.split(f)
            os.rename(f,os.path.join(f[:-1]))
            
        if ("." == f[0]): 
            fipath, finame = os.path.split(f)
            os.rename(f,os.path.join(f[1:]))
        
        plot_file(f)
    
    return
    
    
def collectDirectories(indir):
    dirlist = []
    filelist = []
    
    # print("indir: %s" % (indir))
    
    for x in os.scandir(indir): 
        if (x.is_dir()): 
            dirlist.append(os.path.join(indir,x.name))
        elif (x.is_file()):
            filelist.append(os.path.join(indir,x.name))
            
    return dirlist,filelist

    
def scanBigdata(indir):
    
    if not os.path.isdir(indir):
        print("Sorry, In-Directory %s does not exist!" % (indir))
        sys.exit()
    
    FileList = []
    dirlist_global = []
    rootdir, FileList = collectDirectories(indir)
    if FileList: DoSomethingWithFiles(FileList)
    
    subdir = []
    subsubdir = []
    subsubsubdir = []
    lastDepthdir = []
    
    if (rootdir): # not a File List
        for x in rootdir: 
            subdir, FileList = collectDirectories(x)
            if (subdir): 
                for y in subdir:
                    subsubdir,FileList = collectDirectories(y)
                    if (subsubdir):
                        for z in subsubdir:
                            subsubsubdir,FileList = collectDirectories(z)
                            if (subsubsubdir): 
                                for q in subsubsubdir:
                                    lastDepthdir,FileList = collectDirectories(q)
                                    if (lastDepthdir): print("Sorry, but stopping here, too much depth for %s." % (q))
                                    elif (FileList): DoSomethingWithFiles(FileList,)
                            elif (FileList): DoSomethingWithFiles(FileList)
                    elif (FileList): DoSomethingWithFiles(FileList)
            elif (FileList): DoSomethingWithFiles(FileList)
        
    return

if __name__=="__main__":
    
    if (len(sys.argv) < 2):
        print("Usage: python3 %s %s" % (__file__," indir"))
        sys.exit()
        
    INDIR = sys.argv[1]
    
    if not os.path.isdir(INDIR):
        print("Sorry, In-Directory %s does not exist!" % (INDIR))
        sys.exit()
    
    scanBigdata(INDIR)
    
    sys.exit()

