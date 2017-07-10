# The import of seccomp is copied from https://github.com/seccomp/libseccomp/blob/master/src/python/seccomp.pyx
# Comments are intentionally deleted. Go to libseccomp for details.

from libc.stdint cimport uint8_t, uint32_t, uint64_t
from posix.fcntl cimport O_WRONLY, O_RDWR

cdef extern from "seccomp.h":

    cdef struct scmp_version:
        unsigned int major
        unsigned int minor
        unsigned int micro

    ctypedef void* scmp_filter_ctx

    cdef enum:
        SCMP_ARCH_NATIVE
        SCMP_ARCH_X86
        SCMP_ARCH_X86_64
        SCMP_ARCH_X32
        SCMP_ARCH_ARM
        SCMP_ARCH_AARCH64
        SCMP_ARCH_MIPS
        SCMP_ARCH_MIPS64
        SCMP_ARCH_MIPS64N32
        SCMP_ARCH_MIPSEL
        SCMP_ARCH_MIPSEL64
        SCMP_ARCH_MIPSEL64N32
        SCMP_ARCH_PARISC
        SCMP_ARCH_PARISC64
        SCMP_ARCH_PPC
        SCMP_ARCH_PPC64
        SCMP_ARCH_PPC64LE
        SCMP_ARCH_S390
        SCMP_ARCH_S390X

    cdef enum scmp_filter_attr:
        SCMP_FLTATR_ACT_DEFAULT
        SCMP_FLTATR_ACT_BADARCH
        SCMP_FLTATR_CTL_NNP
        SCMP_FLTATR_CTL_TSYNC
        SCMP_FLTATR_API_TSKIP

    cdef enum scmp_compare:
        SCMP_CMP_NE
        SCMP_CMP_LT
        SCMP_CMP_LE
        SCMP_CMP_EQ
        SCMP_CMP_GE
        SCMP_CMP_GT
        SCMP_CMP_MASKED_EQ

    cdef enum:
        SCMP_ACT_KILL
        SCMP_ACT_TRAP
        SCMP_ACT_ALLOW
    unsigned int SCMP_ACT_ERRNO(int errno)
    unsigned int SCMP_ACT_TRACE(int value)

    ctypedef uint64_t scmp_datum_t

    cdef struct scmp_arg_cmp:
        unsigned int arg
        scmp_compare op
        scmp_datum_t datum_a
        scmp_datum_t datum_b

    scmp_version *seccomp_version()

    scmp_filter_ctx seccomp_init(uint32_t def_action)
    int seccomp_reset(scmp_filter_ctx ctx, uint32_t def_action)
    void seccomp_release(scmp_filter_ctx ctx)

    int seccomp_merge(scmp_filter_ctx ctx_dst, scmp_filter_ctx ctx_src)

    uint32_t seccomp_arch_resolve_name(char *arch_name)
    uint32_t seccomp_arch_native()
    int seccomp_arch_exist(scmp_filter_ctx ctx, int arch_token)
    int seccomp_arch_add(scmp_filter_ctx ctx, int arch_token)
    int seccomp_arch_remove(scmp_filter_ctx ctx, int arch_token)

    int seccomp_load(scmp_filter_ctx ctx)

    int seccomp_attr_get(scmp_filter_ctx ctx,
                         scmp_filter_attr attr, uint32_t* value)
    int seccomp_attr_set(scmp_filter_ctx ctx,
                         scmp_filter_attr attr, uint32_t value)

    char *seccomp_syscall_resolve_num_arch(int arch_token, int num)
    int seccomp_syscall_resolve_name_arch(int arch_token, char *name)
    int seccomp_syscall_resolve_name_rewrite(int arch_token, char *name)
    int seccomp_syscall_resolve_name(char *name)
    int seccomp_syscall_priority(scmp_filter_ctx ctx,
                                 int syscall, uint8_t priority)

    int seccomp_rule_add(scmp_filter_ctx ctx, uint32_t action,
                         int syscall, unsigned int arg_cnt, ...)
    int seccomp_rule_add_array(scmp_filter_ctx ctx,
                               uint32_t action, int syscall,
                               unsigned int arg_cnt,
                               scmp_arg_cmp *arg_array)
    int seccomp_rule_add_exact(scmp_filter_ctx ctx, uint32_t action,
                               int syscall, unsigned int arg_cnt, ...)
    int seccomp_rule_add_exact_array(scmp_filter_ctx ctx,
                                     uint32_t action, int syscall,
                                     unsigned int arg_cnt,
                                     scmp_arg_cmp *arg_array)

    int seccomp_export_pfc(scmp_filter_ctx ctx, int fd)
    int seccomp_export_bpf(scmp_filter_ctx ctx, int fd)


def SCMP_CMP(arg, op, datum_a, datum_b = 0):
    cdef scmp_arg_cmp _arg
    _arg.arg = arg
    _arg.op = op
    _arg.datum_a = datum_a
    _arg.datum_b = datum_b
    return _arg


def seccomp_rule_general(allow_exe, blacklist, special_blacklist):
    """

    :param allow_exe: the allowed path during execve
    :param blacklist: normal blacklist (totally forbidden)
    :param special_blacklist: execve and open (special)
    :return:
    """
    cdef bytes py_bytes = allow_exe.encode()
    cdef char* allow_exe_c_string = py_bytes

    ctx = seccomp_init(SCMP_ACT_ALLOW)
    if not ctx:
        raise OSError("Seccomp init failed")

    for func in blacklist:
        if seccomp_rule_add(ctx, SCMP_ACT_KILL, seccomp_syscall_resolve_name(func.encode()), 0):
            raise OSError("Add rule for %s failed" % func)

    cdef scmp_arg_cmp c_arg

    if "execve" in special_blacklist:
        c_arg = SCMP_CMP(0, SCMP_CMP_NE, <scmp_datum_t>allow_exe_c_string)
        if seccomp_rule_add(ctx, SCMP_ACT_KILL, seccomp_syscall_resolve_name("execve"), 1, c_arg):
            raise OSError("Add rule for execve failed")

    if "open" in special_blacklist:
        c_arg = SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_WRONLY, O_WRONLY)
        if seccomp_rule_add(ctx, SCMP_ACT_KILL, seccomp_syscall_resolve_name("open"), 1, c_arg):
            raise OSError("Add rule for IO failed")
        c_arg = SCMP_CMP(1, SCMP_CMP_MASKED_EQ, O_RDWR, O_RDWR)
        if seccomp_rule_add(ctx, SCMP_ACT_KILL, seccomp_syscall_resolve_name("open"), 1, c_arg):
            raise OSError("Add rule for IO failed")

    if seccomp_load(ctx):
        raise OSError("Seccomp load failed")
    seccomp_release(ctx)

