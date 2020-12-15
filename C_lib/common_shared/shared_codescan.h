#ifndef CODE_SCANNER_SHARED_CODESCAN_H
#define CODE_SCANNER_SHARED_CODESCAN_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <vector>

#include "FromTo.h"

// Contains: public header for codescanner and routinescanner

#define number_of_coderegions_allowed (20)
#define number_of_routines_allowed (1000)

typedef struct _CodescanVector
{
    FromTo* data;
    size_t size;
} CodescanVector, *PCodescanVector;
 
// Only code regions have a bitness und architecture set not NULL.
typedef struct _CodescanOutput
{
    std::vector<FromTo> ascii;
    std::vector<FromTo> zeroblock;
    std::vector<FromTo> highEntropy;
    std::vector<FromTo> genericData;
    std::vector<FromTo> coderegions;
} CodescanOutput, *PCodescanOutput;

// This is the special sauce for the Python binding.
typedef struct _CodescanOutputPy
{
    CodescanVector ascii;
    CodescanVector zeroblock;
    CodescanVector highEntropy;
    CodescanVector genericData;
    CodescanVector coderegions;
} CodescanOutputPy, *PCodescanOutputPy;


// +Codescanner+
// 
// Your first needed routine: 
// initialize libcodescan.so by telling where your languages directory is. 
// Important: the directory needs to be named 'languages'.
// The Codescanner core will not do anything if you do not adhere to this naming rule. ;)
// 
// Args:
// 1. param: __in const char * filepathname   <= path to 'languages' directory.
// returns: STATUS_SUCCESS (0) if success, an error code otherwise.
extern "C" uint32_t initLangPath(const char * CS_Langpath) __attribute__ ((visibility ("default") ));


// +Codescanner+
// 
// Args: 
// 1. __in Filepathname            <= a const char * 
// 2. __in PFromTo FileRegion      <= a pointer to this struct. The file region can span from 0 to filesize, or a custom range.
// 3. __out a PCodescanOutput pOutput <= to be filled with routines. typedef above.
// 4. __in_opt bool aggressive mode (defaults to 0/'not aggressive')
// returns: STATUS_SUCCESS (0) if success, an error code otherwise.
extern "C" uint32_t codescan(   
                            const char * finame, 
                            PFromTo pFileRegion, 
                            PCodescanOutput pOutput,
                            uint8_t aggressive) __attribute__ ((visibility ("default") ));
    
// +Codescanner (Python/extra)+
// Allocates an CodescanOutput structure (initialized with zeros) and 
// returns the codescan in a CodescanOutputPy struct.
// The so-allocated CodescanOutput structure needs to be freed afterwards.
// This is used ONLY for the C/Python binding, not for normal usage.
// 
// Args: 
// 1. __in Filepathname            <= a const char * 
// 2. __in PFromTo FileRegion      <= a pointer to this struct. The file region can span from 0 to filesize, or a custom range.
// 3. __out a CodescanOutput pOutput <=  typedef above. This is what needs to be freed.
// 4. __out a CodescanOutputPy pOutput <=  typedef above.
// 5. __in_opt bool aggressive mode (defaults to 0/'not aggressive')
// 
// returns: 0 if success, an error code otherwise.

extern "C"  uint32_t new_CodescanOutput(const char * finame, 
                                    PFromTo pFileRegion, 
                                    PCodescanOutput raw_output,
                                    PCodescanOutputPy pOutput_python,
                                    uint8_t aggressive) __attribute__ ((visibility ("default") ));
                                    
                                    
// +Codescanner (Python/extra)+
// Frees the CodescanOutput structure given as input argument.
// Args: 
// 1. param: __in PCodescanOutput pointer.
// returns: nothing
// NOTE: normal c/c++ users do NOT need to call this. 
//       You do NOT need to free anything.
//       This is special sauce used in 
//       the C/Python binding (codescanner_analysis) because of 
//       the special requirements of Python.
extern "C"  void free_CodescanOutput(PCodescanOutput pOutput) __attribute__ ((visibility ("default")));


// +Routinescanner+
// 
// Scans a given region for routines and return them in a routines FromTo vector.
// The input to-be-scanned region can be from anywhere, IDA Pro or Codescanner or different.
// 
// Args:
// 1. __in Filepathname            <= a const char * 
// 2. __in PFromTo Coderegion      <= a pointer to this struct, not struct itself.
// 3. __out a std::vector<FromTo> * routinevector  <= to be filled with routines. (a pointer)
// returns: a STATUS value, STATUS_SUCCESS, or an error code otherwise.
// remarks: the coderegion does not need to be from Codescanner. (E.g., can be from IDA Pro).
//          However, it needs to use Codescanner CPU architecture string terminology.
// This simple api function calls subsequently the extended ('Ex') version.
extern "C"  uint32_t scanCodeRegion(
                                const char * finame, 
                                PFromTo pRegion, 
                                std::vector<FromTo> * routinevector) __attribute__ ((visibility ("default") ));
                                
// +Routinescanner (extended)+
// 
// Args: 
// 1. __in Filepathname            <= a const char * 
// 2. __in PFromTo Coderegion      <= a pointer to a _FromTo struct.
// 3. __out a std::vector<FromTo> * routinevector  <= to be filled with routines. (pointer)
// 4. __out a std::vector<uint32_t> * calljump_targets  <= file offsets. (pointer)
// returns: a STATUS value, STATUS_SUCCESS, or an error code otherwise.
// remarks: the coderegion does not need to be from Codescanner. 
//          However, it needs to use Codescanner CPU architecture string terminology.
// The 'Extended' version also outputs all file offsets where jump/call targets have been found in a subroutine.
// Such a jump/call target would itself be a DWORD. 
// The vector contains the file offset, where this DWORD can be found in the file.
// This type of information is usable for different purposes, among them: a recursive disassembler.
extern "C"  uint32_t scanCodeRegionEx(
                                const char * finame, 
                                PFromTo pRegion, 
                                std::vector<FromTo> * routinevector, 
                                std::vector<uint32_t> * calljump_targets) __attribute__ ((visibility ("default") ));


// STATUS code values

// Operation is considered a (full) success.
#define STATUS_SUCCESS    (0)

// Something wrong with the file (does not exist, or null-sized)
#define ERROR_FILE        (1)

// Programming error detected
#define ERROR_IN_ENGINE   (2)  // Report to author

// Codescannerpath is too long as string.
#define ERROR_CODESCANNER_PATH_TOO_LONG_OR_SHORT   (3)

// The input given by the user is bad. 
#define ERROR_USERINPUT_WRONG   (4) 

// Out of memory is very unlikely to ever happen but thinkable.
#define ERROR_OUT_OF_MEMORY    (5)

// This operation is unsupported. Request it if you want it. Otherwise, this is like ERROR_USERINPUT_WRONG.
#define ERROR_UNSUPPORTED_OPERATION  (6)

#endif
