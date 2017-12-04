# Copyright: 2006-2011 Brian Harring <ferringb@gmail.com>
# License: GPL2/BSD

"""
base class to derive from for domain objects

Bit empty at the moment
"""

__all__ = ("MissingFile", "Failure", "domain")

from snakeoil import klass
from snakeoil.demandload import demandload

from pkgcore.config.errors import BaseError

demandload(
    'pkgcore.operations:domain@domain_ops',
    'pkgcore.repository.util:RepositoryGroup',
)


class MissingFile(BaseError):
    """Required file is missing."""
    def __init__(self, filename, setting):
        BaseError.__init__(
            self, "setting %s points at %s, which doesn't exist."
            % (setting, filename))
        self.file, self.setting = filename, setting


class Failure(BaseError):
    """Generic domain failure."""
    def __init__(self, text):
        BaseError.__init__(self, "domain failure: %s" % (text,))
        self.text = text


# yes this is basically empty. will fill it out as the base is better
# identified.
class domain(object):

    fetcher = None
    tmpdir = None
    _triggers = ()

    def _mk_nonconfig_triggers(self):
        return ()

    @property
    def triggers(self):
        l = [x.instantiate() for x in self._triggers]
        l.extend(self._mk_nonconfig_triggers())
        return tuple(l)

    @property
    def repo_configs(self):
        """All defined repo configs."""
        return tuple(r.config for r in self.available_repos
                     if getattr(r, 'config', False))

    @property
    def available_repos(self):
        """Group of all available repos."""
        return self.source_repos + self.installed_repos

    @property
    def available_repos_raw(self):
        """Group of all available repos without filtering."""
        return self.source_repos_raw + self.installed_repos

    @klass.jit_attr_none
    def source_repos(self):
        """Group of all repos."""
        return RepositoryGroup(self.repos)

    @klass.jit_attr_none
    def source_repos_raw(self):
        """Group of all repos without filtering."""
        return RepositoryGroup(self.repos_raw.itervalues())

    @klass.jit_attr_none
    def configured_repos(self):
        """Group of all repos bound with configuration data."""
        return RepositoryGroup(self.repos_configured.itervalues())

    @klass.jit_attr_none
    def installed_repos(self):
        """Group of all installed repos (vdb)."""
        return RepositoryGroup(self.vdb)

    # multiplexed repos
    all_repos = klass.alias_attr("available_repos.combined")
    all_repos_raw = klass.alias_attr("available_repos_raw.combined")
    all_source_repos = klass.alias_attr("source_repos.combined")
    all_source_repos_raw = klass.alias_attr("source_repos_raw.combined")
    all_configured_repos = klass.alias_attr("configured_repos.combined")
    all_installed_repos = klass.alias_attr("installed_repos.combined")

    def pkg_operations(self, pkg, observer=None):
        return pkg.operations(self, observer=observer)

    def build_pkg(self, pkg, observer, clean=True, **format_options):
        return self.pkg_operations(pkg, observer=observer).build(
            observer=observer, clean=clean, **format_options)

    def install_pkg(self, newpkg, observer):
        return domain_ops.install(self, self.all_installed_repos, newpkg,
            observer, self.triggers, self.root)

    def uninstall_pkg(self, pkg, observer):
        return domain_ops.uninstall(self, self.all_installed_repos, pkg, observer,
            self.triggers, self.root)

    def replace_pkg(self, oldpkg, newpkg, observer):
        return domain_ops.replace(self, self.all_installed_repos, oldpkg, newpkg,
            observer, self.triggers, self.root)
