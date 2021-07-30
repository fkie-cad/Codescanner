#include <unistd.h> 
#include <stdint.h>
#include <stdio.h> 
#include <string.h>
#include <stdlib.h>
#include <cstring>
#include <vector>

#include "common_shared/shared_codescan.h"

// Compile with:

// Default:
// gcc -L. -Wl,-rpath=. -o program -fPIC -Ofast -lstdc++ -lcodescan codescandemo.cpp 

    // for ASAN please append: -fno-omit-frame-pointer -fsanitize=address -fsanitize=leak -lasan
    //   But remember, that makes it slow!
    //   Don't do this on a Hardened Arch Linux branch, the shadow memory 
    //   is already used for other purposes on the Hardened branch.

// Debug/gdb build
// gcc -ggdb -rdynamic -L. -Wl,-rpath=. -o program -fPIC -Ofast -lstdc++ -lcodescan codescandemo.cpp

int main(int argc, char **argv)
{
    CodescanOutput Output;
    FromTo Fileregion;
    uint32_t status = STATUS_SUCCESS; 
    int n=0,i=0,j=0;
    const char * finame;
    char currentDir[512] = {0};
    
    if (argc < 2)
    {
        printf("usage: %s filepathname\n",argv[0]);
        return 0;
    }
    
    if (!(strlen(argv[1])))
    {
        printf("Filepathname invalid.\n");
        return 0;
    }
    
    status = 0;
    
    if (getcwd(currentDir, 512) == NULL)
    {
        printf("Error getting current dir.\n");
        return 0;
    }
    
    //printf("%s\n",currentDir);
    
    // = Some test file. ============================
    finame = argv[1];
    
    Fileregion.from = 0; // anything < filesize
    Fileregion.to = 0; // filesize, or anything < filesize
    
    // fileregion: the to-be-scanned region of a file. 
    // You MUST initialize the file region; at least with dummy zeros.
    // Initializing with zeros means that you don't want to use custom start and end offsets.
    // Codescanner will then simply scan the whole file, starting at '0' and ending at 'filesize'.
    // 
    // When you specify any other values not null, Codescanner will 
    // use them as start and end offsets for a custom scan range.
    // Example: from = 0x400 , to = 0x6000. Codescanner will do 
    // sanity checks, e.g., if the file has only 0x5000 bytes, the 
    // CS core will return with an adequate error status code. 
    
    
    // First step: language folder location. 
    status = setLangPath(currentDir);
    
    // You can and should always check the status code.
    if (status != STATUS_SUCCESS)
    {
        printf("language folder could not be found.\n");
        return 0;
    }
    
    // You should also do sanity checks on the filesize (0, too small, too big) 
    // which has been omitted to keep the demo code short.
    
    
    // All Codescanner functions are truly threadsafe. 
    // You can invoke as many as codescan calls as you want simulteaneously.
    // (Not done here.)
    status = codescan(finame, &Fileregion, &Output, 1);

    if (status)
    {
        printf("Error %d: codescanner returned error (check shared_codescanner.h)\n", status);
        return 0;
    }
    
    n = Output.coderegions.size();
    
    
    // Let's print the code regions in this small demo program. 
    // (But the other regions might also be interesting. )
    printf("DEMO printout (Nr. %d) (coderegions: %d):\n",j,n);
    
    if (n)
    {
        
        for (i=0;i<n;i++)
        {
            if (Output.coderegions[i].architecture)
            {
                printf("[Code]: 0x%x - 0x%x  %s  (bitness: %d)\n",
                        Output.coderegions[i].from, 
                        Output.coderegions[i].to, 
                        Output.coderegions[i].architecture, 
                        Output.coderegions[i].bitness
                        );
            }
        }
    }
    
    n = Output.genericData.size();
    
    // Deallocating the stdlib++ region vectors in the CS Output struct 
    // is not needed because the stdlib++ already takes care, and 
    // the program already reached the end of its process lifetime. 
    // 
    // But: if your programs runs a longer time, it would make sense 
    // to clear the vectors when you don't need the region vectors anymore.

    Output.coderegions.clear();
    Output.ascii.clear();
    Output.zeroblock.clear();
    Output.highEntropy.clear();
    Output.genericData.clear();
    Output.coderegions.clear();
    
    return 0;
}
