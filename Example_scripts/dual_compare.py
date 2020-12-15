import os,sys,inspect,subprocess
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')

from matplotlib.ticker import MultipleLocator, FuncFormatter
from pylab import (grid,title, sca, xlabel, ylabel, axis, xticks, yticks, axvline, figure, savefig, close, subplots_adjust)
from matplotlib.pyplot import clf, legend

from codescanner_analysis import CodescannerAnalysisData as CAD
from codescanner_analysis import BytePlot as BP
import file_to_array as FA

RESULTFOLDER = "/ram/"
DPI = 90

# Example code

# Description:
# Take two binaries, compare them (like bindiff) and highlight the matching code visually.
# Output goes to RESULTFOLDER, with dpi=DPI.

# The imports assume codescanner_analysis is globally installed (or use virtualenv).
# Or change the imports to your liking.

def sanitize_file_name(file_name, check_existence=True):
    file_name = os.path.expanduser(file_name)
    print(file_name)
    if check_existence and not os.path.isfile(file_name):
        raise IOError('IOError: Source file does not exist: %s' % (file_name))
    return file_name


def generatePngName(filepathname):
    
    short_finame = os.path.split(filepathname)[1]
    finame_template = ""
    fi_splitext = os.path.splitext(short_finame)
    if (fi_splitext[1]):
        finame_template = "%s_%s" % (fi_splitext[0],fi_splitext[1][1:])  # dot-extension
    else:
        finame_template = fi_splitext[0] # Elf-Binaries without dot-extension
        
    pngname = "%s.png" % (finame_template)
    
    return pngname
  
def plotRegion(subplot,BYTES,BYTES_indices,Regions):
    
    for r in Regions:
        code_start = r[0]
        code_end = r[1]
        code_length = r[1]-r[0]
    
        xPoints = BYTES_indices[BYTES_indices >= code_start]
        xPoints = xPoints[xPoints < code_end]
    
        X = BYTES_indices[xPoints] # Offsets of points
        Y = BYTES[xPoints] # Associated values
        
        # Plot as dots with dot_color.
        subplot.plot(X,Y,'.',markerfacecolor="#20a020",markeredgecolor="#10d760")
        del X
        del Y
        del xPoints
    
    return
    
# [Sequence];routine1_id;routine2_id;routinelength1;routinelength2;file1_pos;file2_pos
# 558bec83ec145356-8b351111111157bb;5;1;0x4d;0x4d;0x7e2;0x459
# 04010000536a08ff-d68b3d1111111150;5;1;0x4d;0x4d;0x7f2;0x469
def ParseMatchingCode(file1_bigger, file2_smaller):
        
    CodeMatches_file1 = [] # start, end
    CodeMatches_file2 = [] # start, end

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parser_process = subprocess.Popen([os.path.join(currentdir,"compare"), file1_bigger, file2_smaller], stdout=subprocess.PIPE)
    output = parser_process.communicate()[0].split(b'\n')
    
    if not len(output):
        return [],[]

    for i in range(1,len(output)):
        tokens = output[i].split(b';')
        if not tokens: break
        if (len(tokens) != 7): break
        
        file1_start = int(tokens[5],base=16)
        file1_end = file1_start + 0x10
        # file1_end = int(tokens[3],base=16) + file1_start
        CodeMatches_file1.append((file1_start,file1_end))
        
        file2_start = int(tokens[6],base=16)
        file2_end = file2_start + 0x10
        # file2_end = int(tokens[4],base=16) + file2_start
        CodeMatches_file2.append((file2_start,file2_end))
            
    return CodeMatches_file1,CodeMatches_file2
    
    
def plot_with_matchingCode(pngfilename, plotter1_big, plotter2_small, biggerFile, smallersizeFile, custom_dpi=90):
    
    codematches_biggerFile,codematches_smallerFile = ParseMatchingCode(biggerFile, smallersizeFile)
    
    # for x in codematches_biggerFile:
        # print("0x%x - 0x%x" % (x[0],x[1]))
    
    fig = figure(figsize=(16,12))
    # fig.tight_layout()
    
    subplot1 = fig.add_subplot(211) 
    subplot2 = fig.add_subplot(212) 
    
    BYTES = FA.load(biggerFile)
    if BYTES is None:
        print("Plot error: file %s not found." % (biggerFile))
        return
    
    # Byte offsets.
    BYTES_indices = np.arange(0,BYTES.size)
    
    # subplot.axis('off')
    plotter1_big._generate_plot(BYTES, BYTES_indices, subplot1)
    
    plotRegion(subplot1, BYTES,BYTES_indices, codematches_biggerFile)
    
    del BYTES
    del BYTES_indices
    
    BYTES_SMALLER_FILE = FA.load(smallersizeFile)
    smallfileEnd = BYTES_SMALLER_FILE.size
    
    if BYTES_SMALLER_FILE is None:
        print("Plot error: file %s not found." % (smallersizeFile))
        return
    
    # Byte offsets.
    BYTES_indices = np.arange(0,plotter1_big._file_size)
    
    BYTES = np.zeros((plotter1_big._file_size),dtype=np.uint32)
    BYTES[:smallfileEnd] = BYTES_SMALLER_FILE
    
    plotter2_small._file_size = plotter1_big._file_size
    
    plotter2_small._generate_plot(BYTES, BYTES_indices, subplot2)
    
    plotRegion(subplot2, BYTES,BYTES_indices, codematches_smallerFile)
    
    subplot2.set_title('{} ({} kB)'.format(plotter2_small._short_filename, round(1.0 * (smallfileEnd / 1024))))
    axvline(x=smallfileEnd, ymin=0, ymax=255,linewidth=6.0, color='r')
    axvline(x=smallfileEnd, ymin=0, ymax=255,linewidth=2.0, color='k')
    
    subplot2.add_patch(matplotlib.patches.Rectangle((smallfileEnd,0.0), (plotter1_big._file_size - smallfileEnd), 255, fill=True, color="#cccccc"))
    
    for ax in fig.axes:
        matplotlib.pyplot.sca(ax)
        xticks(rotation=315)
    
    subplots_adjust(left=0.1, right=0.9,top=0.9,bottom=0.1,wspace=0.3, hspace=0.3)
    
    del BYTES
    del BYTES_SMALLER_FILE
    del BYTES_indices
    
    legend(loc='upper right')
    
    # Extra wishes to Matplotlib: 
    #    don't waste so much white space, and put the legend to upper right.
    
    savefig("/ram/%s" % (pngfilename), dpi=custom_dpi)
    close(fig)
    time.sleep(0.5)
    
    clf()
    
    return
            
        

if __name__=="__main__":
    
    if (len(sys.argv) < 3):
        print("Usage: %s %s" % (sys.argv[0]," binary1 binary2 (shortPngname)"))
        sys.exit()
        
    finamepath1 = str(sys.argv[1])
    finamepath2 = str(sys.argv[2])
    
    pngfilename = "out.png"
    
    if (len(sys.argv) == 4):
        
        pngfilename = str(sys.argv[3])
        
        if (len(pngfilename) < 5):
            print("pngfilename is bad!")
            sys.exit()
            
        if not (pngfilename[-4:] == ".png"):
            print("pngfilename is bad!")
            sys.exit()
    
    finamepath1 = sanitize_file_name(finamepath1, check_existence=True)
    finamepath2 = sanitize_file_name(finamepath2, check_existence=True)
    
    finamesize1 = os.path.getsize(finamepath1)
    finamesize2 = os.path.getsize(finamepath2)
    
    biggersize = 0
    biggerFile = ""
    smallersize = 0
    smallersizeFile = ""
    
    if (finamesize1 > finamesize2):
        
        biggersize = finamesize1
        smallersize = finamesize2
        
        biggerFile = finamepath1
        smallersizeFile = finamepath2
        
    else:
        biggersize = finamesize2
        smallersize = finamesize1
        
        biggerFile = finamepath2
        smallersizeFile = finamepath1
    
    cad_bigger = None
    cad = None
    
    cad = CAD(smallersizeFile,0,smallersize)
    if cad is None:
        print("error: cad object is None!")
        sys.exit()
        
    cad_bigger = CAD(biggerFile,0,biggersize)
    if cad_bigger is None:
        print("error: cad object is None!")
        sys.exit()
        
    print(cad.decision)
    print(cad.file_header)
    print(cad.architecture)
    
    print(cad_bigger.decision)
    print(cad_bigger.file_header)
    print(cad_bigger.architecture)
    
    plotter2_small = cad._init_plotter(1)
    plotter1_big = cad_bigger._init_plotter(1)
    
    plot_with_matchingCode(pngfilename, plotter1_big, plotter2_small, biggerFile, smallersizeFile, custom_dpi=DPI)
    
    sys.exit()
