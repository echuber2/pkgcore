# Copyright: 2005 Gentoo Foundation
# Author(s): Brian Harring (ferringb@gentoo.org)
# License: GPL2
# $Id: __init__.py 2189 2005-10-25 21:49:47Z ferringb $
from portage.repository import multiplex
from repository import tree as vdb_repository
from virtualrepository import tree as virtualrepository

def repository(*args, **kwargs):
	r = vdb_repository(*args, **kwargs)
	return multiplex.tree(r, virtualrepository(r))
