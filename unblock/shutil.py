import shutil as shutil_sync
from .core import asyncify_func

copyfileobj = asyncify_func(shutil_sync.copyfileobj)
copyfile = asyncify_func(shutil_sync.copyfile)
copymode = asyncify_func(shutil_sync.copymode)
copystat = asyncify_func(shutil_sync.copystat)
copy = asyncify_func(shutil_sync.copy)
copy2 = asyncify_func(shutil_sync.copy2)
copytree = asyncify_func(shutil_sync.copytree)
rmtree = asyncify_func(shutil_sync.rmtree)
move = asyncify_func(shutil_sync.move)
disk_usage = asyncify_func(shutil_sync.disk_usage)
chown = asyncify_func(shutil_sync.chown)
which = asyncify_func(shutil_sync.which)
make_archive = asyncify_func(shutil_sync.make_archive)
unpack_archive = asyncify_func(shutil_sync.unpack_archive)
get_terminal_size = asyncify_func(shutil_sync.get_terminal_size)

#direct invoke
get_archive_formats = shutil_sync.get_archive_formats
register_archive_format = shutil_sync.register_archive_format
unregister_archive_format = shutil_sync.unregister_archive_format
register_unpack_format = shutil_sync.register_unpack_format
unregister_unpack_format = shutil_sync.unregister_unpack_format
get_unpack_formats = shutil_sync.get_unpack_formats