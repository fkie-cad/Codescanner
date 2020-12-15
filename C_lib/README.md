# Codescanner (core) #

The Codescanner detects machine code in files and identifies the cpu architecture, endianness, and bitness.
It can be used against data files (pdf, jpgs, unknown binary files).

Version: 1.2.3  
## Codescanner

Last changed: 10. Dec. 2020

### What this is

This is the Codescanner core, in standalone binary form (`codescan`) and
as thread-safe library (`libcodescan.so`). The library form is also used 
in the Python2/3 `codescanner_analysis`.

### Author and copyright information

Copyright © Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e.V.   
All rights reserved.   
Author: Viviane

Please read the included LICENSE. This program is free for academic use and research.   
In case you want to use it in a commercial project you can write an email.

### Requirements
* none

### Usage of `codescan`

```
$ ./codescan filepathname
```

Optional arguments:

```
$ ./codescan filepathname [s=startAddress] [e=endAddress] [a=1]

```

The offsets can be given in decimal form or in hexadecimal form. `a=1` 
enables the aggressive mode. The aggressive mode searches for machine code with
more enthusiasm, but will produce more False Positives (on true data files).
Defaults to non-agressive mode.

### Usage of the library form

Check `codescandemo.cpp` for a full and commented code example.
The C/C++ headers can be found in common_shared and contain the documented API.

The library is fully *thread-safe* and compatible to both ansi C and C++ code.

### Bug-reporting

Please do report any bugs in the issues. 
It has been checked with ASAN. There are no known memory leaks or buffer overflows. 
Disclaimer: the author would be amazed if there was a memory leak or buffer 
overflow, but would fix them at IRQL > 0 if they were reported. (Yes, this is a challenge.)
