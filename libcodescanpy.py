# -*- coding: utf-8 -*-
import sys,os
import ctypes

LITTLE_ENDIAN = 1
BIG_ENDIAN = 2

RESULT_DICT = 1
RESULT_LIST = 2

STATUS = {
            0: "STATUS_SUCCESS", 
            1: "ERROR_FILE",
            2: "ERROR_IN_ENGINE",
            3: "ERROR_CODESCANNER_PATH_TOO_LONG_OR_SHORT",
            4: "ERROR_USERINPUT_WRONG",
            5: "ERROR_OUT_OF_MEMORY",
            6: "ERROR_UNSUPPORTED_OPERATION"
         }

class FromTo(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint32),  # from changed to start, cause it's a keyword in python
                ("end", ctypes.c_uint32),  # to changed to end for convenience
                ("bitness", ctypes.c_uint32),
                ("endianess", ctypes.c_uint32),
                ("architecture", ctypes.c_char_p)
                ]


class CppStdVector(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(FromTo)),
                ("size", ctypes.c_size_t)
                ]


class CodescanOutput(ctypes.Structure):
    _fields_ = [("ascii", CppStdVector),
                ("zeroblock", CppStdVector),
                ("highEntropy", CppStdVector),
                ("genericData", CppStdVector),
                ("coderegions", CppStdVector)
                ]

# THE ansi c library (libcodescan.so)
libcodescan = None

def init():
    
    global libcodescan
    selfDirectory = os.path.dirname(os.path.realpath(__file__))
    libcodescan_path = os.path.join(selfDirectory, 'res/lib', 'libcodescan.so')
    lang_path = os.path.join(selfDirectory, 'res/lib')
    
    try:
        libcodescan = ctypes.CDLL(libcodescan_path)
    except:
        print("Loading libcodescan.so failed! Expected path: %s." % (libcodescan_path))
        sys.exit()

    libcodescan.setLangPath.argtypes = [ctypes.c_char_p]
    libcodescan.setLangPath.restype = ctypes.c_int

    libcodescan.free_CodescanOutput.argtypes = [ctypes.c_void_p]
    libcodescan.free_CodescanOutput.restype = None
    
    libcodescan.new_CodescanOutput.argtypes = [ctypes.c_char_p, ctypes.POINTER(FromTo), ctypes.c_void_p, ctypes.POINTER(CodescanOutput), ctypes.c_uint8]
    libcodescan.new_CodescanOutput.restype = ctypes.c_int

    c_lang_path = ctypes.c_char_p(lang_path.encode("utf-8"))
    status = libcodescan.setLangPath(c_lang_path)
    
    if (status != 0):
        print("Core error %d (fatal): loading language files failed! Expected path: %s." % (status,lang_path))
        sys.exit()


def scan(file_src, start=0, end=0, bool_aggressive=0, r_type=RESULT_DICT):
    
    if not (os.path.isfile(file_src)):
        raise IOError("(scan:) File '%s' is not existent!" % (file_src) )
        
    if ((os.path.getsize(file_src)) < 1):
        raise IOError("(scan:) File '%s' is a NULL sized file!" % (file_src) )
    
    # print("scan(%s, %d, %d)" % (file_src, start, end))
    
    c_file_src = ctypes.c_char_p(file_src.encode("utf-8"))
    c_start = ctypes.c_uint32(start)
    c_end = ctypes.c_uint32(end)
    
    c_bitness = ctypes.c_uint32(0)
    c_endianess = ctypes.c_uint32(0)
    c_architecture = None
    
    c_aggressive = ctypes.c_uint8(bool_aggressive)

    c_scan_region = FromTo(c_start, c_end, c_bitness, c_endianess, c_architecture)
    
    c_output = CodescanOutput()
    
    raw_data_ptr = ctypes.c_void_p(0)
    
    status = libcodescan.new_CodescanOutput(c_file_src, c_scan_region, raw_data_ptr, c_output, c_aggressive)

    if (status != 0):
        # If there is an error any data that has been allocated has already been freed.
        # Do not try to free it.
        print("Core error '%s' (fatal): Codescan failed!" % (STATUS[status]))
        sys.exit()

    # print("success")
    # print(" - ascii")
    # for i in range(c_output.ascii.size):
    #     r = c_output.ascii.data[i]
    #
    #     print(" (%d) - %d : %d (%d, %d, %s)" % (i, r.start, r.end, r.bitness, r.endianess, r.architecture))
    # print(" - coderegions")
    # for i in range(c_output.coderegions.size):
    #     r = c_output.ascii.data[i]
    #
    #     print(" (%d) - %d : %d (%d, %d, %s)" % (i, r.start, r.end, r.bitness, r.endianess, r.architecture))

    result = {}
    
    if r_type == RESULT_DICT:
        if c_output.ascii.size > 0:
            result["Ascii"] = _convert_to_dict(c_output.ascii)
        if c_output.genericData.size > 0:
            result["Data"] = _convert_to_dict(c_output.genericData)
        if c_output.highEntropy.size > 0:
            result["HighEntropy"] = _convert_to_dict(c_output.highEntropy)
        if c_output.coderegions.size > 0:
            result["Code"] = _convert_to_dict(c_output.coderegions)
        if c_output.zeroblock.size > 0:
            result["Zero"] = _convert_to_dict(c_output.zeroblock)
            
    elif r_type == RESULT_LIST:
        if c_output.ascii.size > 0:
            result["Ascii"] = _convert_to_list(c_output.ascii)
        if c_output.genericData.size > 0:
            result["Data"] = _convert_to_list(c_output.genericData)
        if c_output.highEntropy.size > 0:
            result["HighEntropy"] = _convert_to_list(c_output.highEntropy)
        if c_output.coderegions.size > 0:
            result["Code"] = _convert_to_list(c_output.coderegions)
        if c_output.zeroblock.size > 0:
            result["Zero"] = _convert_to_list(c_output.zeroblock)

    if (raw_data_ptr): libcodescan.free_CodescanOutput(raw_data_ptr)

    return result


def _convert_to_dict(cs_region):
    if cs_region.size == 0:
        return ()

    regions = []
    for i in range(cs_region.size):
        cs_r = cs_region.data[i]

        r = {"from": int(cs_r.start), "to": int(cs_r.end), "bitness": int(cs_r.bitness), "endianess": int(cs_r.endianess), "architecture": cs_r.architecture}
        if r['architecture'] is not None:
            r['architecture'] = r['architecture'].decode("utf-8")
        regions.append(r)

    return regions


def _convert_to_list(cs_region):
    if cs_region.size == 0:
        return []

    regions = []
    for i in range(cs_region.size):
        cs_r = cs_region.data[i]

        if cs_r.architecture is not None:
            r = [int(cs_r.start), int(cs_r.end), cs_r.architecture.decode("utf-8"), int(cs_r.bitness), int(cs_r.endianess)]
        else:
            r = [int(cs_r.start), int(cs_r.end)]
        regions.append(r)

    return regions
