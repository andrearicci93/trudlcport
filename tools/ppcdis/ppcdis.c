/* ppcdis: disassembla PowerPC Xbox 360 (con VMX128) da un'immagine piatta (base 0x82000000).
   Usa il disassemblatore binutils di XenonRecomp (tools/xenonrecomp/src/thirdparty/disasm), dialetto "cell" (include VMX_128).
   uso: ppcdis FILE.bin INDIRIZZO_HEX N_ISTRUZIONI */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "dis-asm.h"
static char line[512]; static size_t pos;
static int pf(FILE *s, const char *fmt, ...) { va_list ap; va_start(ap, fmt); int n = vsnprintf(line + pos, sizeof line - pos, fmt, ap); va_end(ap); if (n > 0) pos += n; return n; }
static void pa(bfd_vma a, struct disassemble_info *i) { pf(NULL, "0x%08llx", (unsigned long long)a); }
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "uso: ppcdis FILE ADDR N\n"); return 1; }
    FILE *f = fopen(argv[1], "rb"); if (!f) { perror(argv[1]); return 1; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *buf = malloc(sz); fread(buf, 1, sz, f); fclose(f);
    unsigned long long base = 0x82000000ULL, a = strtoull(argv[2], NULL, 16); long n = strtol(argv[3], NULL, 10);
    disassemble_info info; INIT_DISASSEMBLE_INFO(info, stdout, pf);
    info.arch = bfd_arch_powerpc; info.mach = bfd_mach_ppc64; info.endian = BFD_ENDIAN_BIG;
    info.buffer = buf; info.buffer_vma = base; info.buffer_length = sz; info.disassembler_options = "cell";
    info.print_address_func = pa;
    for (long k = 0; k < n; k++, a += 4) {
        pos = 0; line[0] = 0;
        unsigned char *w = buf + (a - base);
        print_insn_big_powerpc(a, &info);
        printf("%08llx %02x%02x%02x%02x %s\n", a, w[0], w[1], w[2], w[3], line);
    }
    return 0;
}
