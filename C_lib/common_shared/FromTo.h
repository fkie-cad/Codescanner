#ifndef CODE_SCANNER_FROM_TO_H
#define CODE_SCANNER_FROM_TO_H

#include <stdint.h>

#define cs_bit32   (32)
#define cs_bit64   (64)
#define cs_bit16   (16)

#define cs_no_endianess (0)
#define cs_little_endian (1)
#define cs_big_endian (2)

typedef struct _FromTo
{
    uint32_t from;
    uint32_t to;
    uint32_t bitness;    // 0 for non-code Regions.
    uint32_t endianess;  // 0 for non-code Regions.
    const char * architecture; // with NULL for non-code Regions.
} FromTo, *PFromTo;

#endif
