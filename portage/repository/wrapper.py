# Copyright: 2005 Gentoo Foundation
# License: GPL2
# $Id: wrapper.py 2278 2005-11-10 00:25:26Z ferringb $

# icky.
# ~harring
import prototype, errors

class wrapperTree(prototype.tree):
	"""wrap an existing repository filtering results based upon passed in restrictions."""
	def __init__(self, repo, package_class):
		self.raw_repo = repo
		if not isinstance(self.raw_repo, prototype.tree):
			raise errors.InitializationError("%s is not a repository tree derivative" % str(self.raw_repo))
		self.package_class = package_class
		self.raw_repo = raw_repo
