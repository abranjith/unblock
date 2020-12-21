import os as os_sync
from .core import asyncify, asyncify_x


__io_attrs_to_asynchify = ["ctermid", "environ", "environb", "chdir", "fchdir", "getcwd", "getenv", "getenvb", "get_exec_path", "getegid", "geteuid", "getgid", 
"getgrouplist", "getgroups", "getlogin", "getpgid", "getpgrp", "getpid", "getppid", "getpriority", "getresuid", "getresgid", "getuid", "initgroups", "putenv", 
"setegid", "seteuid", "setgid", "setgroups", "setpgrp", "setpgid", "setpriority", "setregid", "setresgid", "setresuid", "setreuid", "getsid", "setsid", "setuid", 
"strerror", "umask", "uname", "unsetenv", "close", "closerange", "copy_file_range", "device_encoding", "dup", "dup2", "fchmod", "fchown", "fdatasync", "fpathconf", 
"fstat", "fstatvfs", "fsync", "ftruncate", "get_blocking", "isatty", "lockf", "lseek", "open", "openpty", "pipe", "pipe2", "posix_fallocate", "posix_fadvise",
"pread", "preadv", "pwrite", "pwritev", "read", "sendfile", "readv", "tcgetpgrp", "tcsetpgrp", "ttyname", "write", "writev", "get_terminal_size", "access",
"chdir", "chflags", "chmod", "chown", "chroot", "fchdir", "getcwd", "getcwdb", "lchflags", "lchmod", "lchown", "link", "listdir", "lstat", "mkdir", "makedirs",
"mkfifo", "mknod", "pathconf", "readlink", "remove", "removedirs", "rename", "renames", "replace", "rmdir", "statvfs", "symlink", "sync", "truncate", "unlink",
"utime", "memfd_create", "getxattr", "listxattr", "removexattr", "setxattr", "abort"]

__cpu_attrs_to_asynchify = ["fsencode", "fsdecode"]

#TODO - scandir
#TODO - walk, fwalk

#direct invoke by default
def __getattr__(name):
    if not hasattr(os_sync, name):
        raise AttributeError(f"os has no attribute '{name}'")
    attr = getattr(os_sync, name)
    if name in __io_attrs_to_asynchify:
        return asyncify(attr)
    if name in __cpu_attrs_to_asynchify:
        return asyncify_x(attr)
    return attr
