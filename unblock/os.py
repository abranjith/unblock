import os as os_sync
from .core import asyncify, AsyncBase, asyncify_func, AsyncCtxMgrIterBase, AsyncIterBase

class _AsyncCtxIterBase(AsyncCtxMgrIterBase):

    def __init__(self, original_obj, iter_obj_type = None):
        super().__init__(original_obj)
        self._iter_obj_type = iter_obj_type

    @property
    def __attrs_to_asynchify(self):
        return ["close"]

    async def __anext__(self):
        def _next():
            try:
                result = next(self._itrtr)
                if self._iter_obj_type:
                    return self._iter_obj_type(result)
                return result
            except StopIteration:
                raise StopAsyncIteration
        return await asyncify_func(_next)()
    
class AsyncDirEntry(AsyncBase):
    
    @property
    def __attrs_to_asynchify(self):
        return ["inode", "is_dir", "is_file", "is_symlink", "stat"]

async def scandir(*args, **kwargs):
    sd = await asyncify_func(os_sync.scandir)(*args, **kwargs)
    return _AsyncCtxIterBase(sd, AsyncDirEntry)

def walk(*args, **kwargs):
    gtr = os_sync.walk(*args, **kwargs)
    return AsyncIterBase(gtr)

def fwalk(*args, **kwargs):
    gtr = os_sync.fwalk(*args, **kwargs)
    return AsyncIterBase(gtr)

__io_attrs_to_asynchify = ["ctermid", "environ", "environb", "chdir", "fchdir", "getcwd", "getenv", "getenvb", "get_exec_path", "getegid", "geteuid", "getgid", 
"getgrouplist", "getgroups", "getlogin", "getpgid", "getpgrp", "getpid", "getppid", "getpriority", "getresuid", "getresgid", "getuid", "initgroups", "putenv", 
"setegid", "seteuid", "setgid", "setgroups", "setpgrp", "setpgid", "setpriority", "setregid", "setresgid", "setresuid", "setreuid", "getsid", "setsid", "setuid", 
"strerror", "umask", "uname", "unsetenv", "close", "closerange", "copy_file_range", "device_encoding", "dup", "dup2", "fchmod", "fchown", "fdatasync", "fpathconf", 
"fstat", "fstatvfs", "fsync", "ftruncate", "get_blocking", "isatty", "lockf", "lseek", "open", "openpty", "pipe", "pipe2", "posix_fallocate", "posix_fadvise",
"pread", "preadv", "pwrite", "pwritev", "read", "sendfile", "readv", "tcgetpgrp", "tcsetpgrp", "ttyname", "write", "writev", "get_terminal_size", "access",
"chdir", "chflags", "chmod", "chown", "chroot", "fchdir", "getcwd", "getcwdb", "lchflags", "lchmod", "lchown", "link", "listdir", "lstat", "mkdir", "makedirs",
"mkfifo", "mknod", "pathconf", "readlink", "remove", "removedirs", "rename", "renames", "replace", "rmdir", "stat", "statvfs", "symlink", "sync", "truncate", "unlink",
"utime", "memfd_create", "getxattr", "listxattr", "removexattr", "setxattr", "abort", "add_dll_directory", "execl", "execle", "execlp", "execlpe", "execv", "execve",
"execvp", "execvpe", "_exit", "fork", "forkpty", "kill", "killpg", "nice", "pidfd_open", "plock", "popen", "posix_spawn", "posix_spawnp", "register_at_fork",
"spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "startfile", "system", "times", "wait", "waitid", "waitpid", "wait3", "wait4",
"WCOREDUMP", "WIFCONTINUED", "WIFSTOPPED", "WIFSIGNALED", "WIFEXITED", "WEXITSTATUS", "WSTOPSIG", "WTERMSIG", "sched_setscheduler", "sched_getscheduler", "sched_setparam",
"sched_getparam", "sched_rr_get_interval", "sched_yield", "sched_setaffinity", "sched_getaffinity", "confstr", "cpu_count", "getloadavg", "sysconf", "fsencode", "fsdecode", 
"getrandom", "urandom"]

#direct invoke by default
def __getattr__(name):
    if not hasattr(os_sync, name):
        raise AttributeError(f"os has no attribute '{name}'")
    attr = getattr(os_sync, name)
    if name in __io_attrs_to_asynchify:
        return asyncify(attr)
    return attr
