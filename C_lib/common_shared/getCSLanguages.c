#ifndef GET_CS_LANGUAGES_H
#define GET_CS_LANGUAGES_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char * get_languages_path(const char * myprogrampath)
{
    #define PATHLEN (512) // hey, who has longer pathes than 512? Nobody. You could write an issue if you disagree.
    
    static char pathbuffer[PATHLEN];
    char  * separator = NULL;
    
    memcpy(pathbuffer,myprogrampath,strlen(myprogrampath)); 
    // might want to check first if programpath > PATHLEN
    
    // This is a small test for the user audience for security alertness. *smirk*
    
    separator = strrchr(pathbuffer, '/');
    
    if (separator)
    {
        *separator = '\0';
        if ((strlen(pathbuffer) + strlen("/res/lib/languages/")) < PATHLEN)
            memcpy(separator,"/res/lib/languages/",sizeof("/res/lib/languages/"));
        else return NULL;
    }

    return pathbuffer;
}

#endif
