# Bazaar-NG -- distributed version control
#
# Copyright (C) 2006 by Canonical Ltd
# Copyright (C) 2006 by Brian Harring <ferringb@gentooexperimental.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Wrapper for readdir which grabs file type from d_type."""


# the opaque C library DIR type.
cdef extern from 'errno.h':
	int ENOENT
	int errno
	char *strerror(int errno)

cdef extern from 'sys/types.h':
	ctypedef long ssize_t
	ctypedef unsigned long size_t

cdef extern from 'dirent.h':
	int DT_UNKNOWN
	int DT_REG
	int DT_LNK
	int DT_DIR
	int DT_FIFO
	int DT_SOCK
	int DT_CHR
	int DT_BLK
	ctypedef struct dirent:
		char d_name[256]
		# this will fail to compile if d_type is not defined.
		# if this module fails to compile, use the .py version.
		unsigned char d_type
	ctypedef struct DIR
	# should be DIR *, pyrex barfs.
	DIR * opendir(char * name) except NULL
	int closedir(DIR * dir) except -1
	dirent *readdir(DIR *dir)

cdef extern from '_stat.c':
	int isdir(char * path, int followsyms)
	int isreg(char * path, int followsyms)

_directory = 'directory'
_chardev = 'chardev'
_block = 'block'
_file = 'file'
_fifo = 'fifo'
_symlink = 'symlink'
_socket = 'socket'
_unknown = 'unknown'

dot = ord('.')

# add a typedef struct dirent dirent to workaround pyrex
cdef extern from '_readdir.h':
	pass

def cpy_listdir(path):
	cdef DIR *the_dir
	cdef dirent * entry
	cdef char *name
	errno = 0
	the_dir = opendir(path)
	result = []
	try:
		entry = readdir(the_dir)
		while entry != NULL:
			name = entry.d_name
			if not (name[0] == dot and
				(name[1] == 0 or name[1] == dot and name [2] == 0)):
				result.append(name)
			entry = readdir(the_dir)
		if entry == NULL and errno != ENOENT and errno != 0:
			raise OSError(errno, strerror(errno))
	finally:
		closedir(the_dir)
	return result

def cpy_listdir_dirs(path, followSymlinks=True):
	cdef DIR *the_dir
	cdef dirent * entry
	cdef char *name
	cdef int followsyms
	if followSymlinks:
		followsyms = 1
	else:
		followsyms = 0
	errno = 0
	ret = 0
	the_dir = opendir(path)
	result = []
	try:
		entry = readdir(the_dir)
		while entry != NULL:
			name = entry.d_name
			if name[0] == dot and \
				(name[1] == 0 or (name[1] == dot and name [2] == 0)):
				entry = readdir(the_dir)
				continue
			elif entry.d_type == DT_DIR:
				result.append(name)
			elif entry.d_type == DT_UNKNOWN or (followsyms and entry.d_type == DT_LNK):
				fp = path + "/" + name
				ret = isdir(fp, followsyms)
				if ret < 0 or ret:
					result.append(name)
			
			entry = readdir(the_dir)
		if entry == NULL and errno != ENOENT and errno != 0:
			raise OSError(errno, strerror(errno))
	finally:
		closedir(the_dir)
	return result

def cpy_listdir_files(path, followSymlinks=True):
	cdef DIR *the_dir
	cdef dirent * entry
	cdef char *name
	cdef int followsyms
	if followSymlinks:
		followsyms = 1
	else:
		followsyms = 0
	errno = 0
	ret = 0
	the_dir = opendir(path)
	result = []
	try:
		entry = readdir(the_dir)
		while entry != NULL:
			name = entry.d_name
			if name[0] == dot and \
				(name[1] == 0 or (name[1] == dot and name [2] == 0)):
				entry = readdir(the_dir)
				continue
			elif entry.d_type == DT_REG:
				result.append(name)
			elif entry.d_type == DT_UNKNOWN or (followsyms and entry.d_type == DT_LNK):
				fp = path + "/" + name
				ret = isreg(fp, followsyms)
				if ret == 0:
					result.append(name)
			
			entry = readdir(the_dir)
		if entry == NULL and errno != ENOENT and errno != 0:
			raise OSError(errno, strerror(errno))
	finally:
		closedir(the_dir)
	return result
	
	
def read_dir(path):
	"""Like os.listdir, this reads a directories contents.

	:param path: the directory to list.
	:return: a list of (basename, kind) tuples.
	"""
	cdef DIR *the_dir
	# currently this needs a fixup - the C code says 'dirent' but should say
	# 'struct dirent'
	cdef dirent * entry
	cdef char *name 
	errno = 0
	the_dir = opendir(path)
	result = []
	try:
		entry = readdir(the_dir)
		while entry != NULL:
			name = entry.d_name
			if not (name[0] == dot and (
				(name[1] == 0) or 
				(name[1] == dot and name [2] == 0))
				):
				if entry.d_type == DT_UNKNOWN:
					type = _unknown
				elif entry.d_type == DT_REG:
					type = _file
				elif entry.d_type == DT_DIR:
					type = _directory
				elif entry.d_type == DT_FIFO:
					type = _fifo
				elif entry.d_type == DT_SOCK:
					type = _socket
				elif entry.d_type == DT_CHR:
					type = _chardev
				elif entry.d_type == DT_BLK:
					type = _block
				else:
					type = _unknown
				result.append((entry.d_name, type))
			entry = readdir(the_dir)
		if entry == NULL and errno != ENOENT and errno != 0:
			raise OSError(errno, strerror(errno))
	finally:
		closedir(the_dir)
	return result
