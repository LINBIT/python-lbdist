#!/usr/bin/env python
import os
import re


class Distribution(object):
    def __init__(self, osreleasepath='/etc/os-release'):
        self._supported_dist_IDs = ('amzn', 'centos', 'rhel', 'rhcos', 'debian',
                                    'ubuntu', 'xenenterprise', 'ol', 'sles')
        self._osreleasepath = osreleasepath

        self._osrelease = {}
        self._update_osrelease()

        self._name = self._osrelease.get('ID')
        if self._name not in self._supported_dist_IDs:
            raise Exception("Could not determine distribution info")

        self._update_version()
        self._update_family()

    @property
    def osrelease(self):
        return self._osrelease

    def _update_osrelease(self):
        # gernates a slightly oppinionated osrelease dict that is similar to /etc/os-release
        # for very old distris it just sets the bare minimum to determine version and family
        osrelease = {}
        if os.path.exists(self._osreleasepath):
            with open(self._osreleasepath) as o:
                for line in o:
                    line = line.strip()
                    if len(line) == 0 or line[0] == '#':
                        continue
                    k, v = line.split('=')

                    if v.startswith('"') or v.startswith("'"):
                        v = v[1:-1]  # assume they are at least symmetric

                    osrelease[k] = v
            if osrelease.get('ID', '') == 'ol':  # sorry, but you really are...
                osrelease['ID_LIKE'] = 'rhel'

        # centos 6, centos first, as centos has centos-release and redhat-release
        elif os.path.exists('/etc/centos-release'):
            osrelease['ID'] = 'centos'
            osrelease['ID_LIKE'] = 'rhel'
        # rhel 6
        elif os.path.exists('/etc/redhat-release'):
            osrelease['ID'] = 'rhel'

        self._osrelease = osrelease

    def _update_version(self):
        version = None

        if self._name == 'debian':
            try:
                v = self._osrelease['VERSION']
            except KeyError:
                raise Exception('No "VERSION" in your Debian {0}, are you running testing/sid?'.format(self._osreleasepath))

            m = re.search(r'^\d+ \((\w+)\)$', v)
            if not m:
                raise Exception('Could not determine version information for your Debian')
            version = m.group(1)
        elif self._name == 'ubuntu':
            version = self._osrelease['VERSION_CODENAME']
        elif self._name == 'centos':
            line = ''
            with open('/etc/centos-release') as cr:
                line = cr.readline().strip()
            # .* because the nice centos people changed their string between 6 and 7 (added 'Linux')
            m = re.search(r'^CentOS .* ([\d\.]+) \(.*\)$', line)
            if not m:
                raise Exception('Could not determine version information for your Centos')
            version = m.group(1)
        elif self._name == 'amzn':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'rhel':
            try:
                version = self._osrelease['VERSION_ID']
            except KeyError:
                line = ''
                with open('/etc/redhat-release') as cr:
                    line = cr.readline().strip()
                m = re.search(r'^Red Hat Enterprise .* ([\d\.]+) \(.*\)$', line)
                if not m:
                    raise Exception('Could not determine version information for your RHEL6')
                version = m.group(1)
        elif self._name == 'rhcos':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'xenenterprise':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'ol':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'sles':
            version = self._osrelease['VERSION_ID']
        else:
            raise Exception("Could not determine version information")

        self._version = version

    def _update_family(self):
        family = None

        families = ('rhel', 'sles', 'debian')
        if self._name in families:
            family = self._name
        elif 'ID_LIKE' in self._osrelease:
            for i in self._osrelease['ID_LIKE'].split():
                if i in families:
                    family = i
                    break

        if family is None:
            raise Exception("Could not determine family for unknown distribution")
        self._family = family

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def family(self):
        return self._family


class LinbitDistribution(Distribution):
    def __init__(self, osreleasepath):
        super(LinbitDistribution, self).__init__(osreleasepath)

    @property
    def repo_name(self):
        # use '{0}' instead of '{}', RHEL 6 does not handle the modern version
        if self._name in ('debian', 'ubuntu'):
            return '{0}-{1}'.format(self._name, self._version)
        elif self._name in ('rhel', 'centos', 'amzn'):
            d = self._name
            if self._name == 'centos':
                d = 'rhel'
            elif self._name == 'amzn':
                d = 'amazonlinux'

            v = self._version
            if '.' in v:
                v = v.split('.')
                v = v[0] + '.' + v[1]
            else:
                v += '.0'
            return '{0}{1}'.format(d, v)
        elif self._name in ('xenenterprise', 'ol'):
            d = self._name
            if self._name == 'xenenterprise':
                d = 'xenserver'
            v = self._version
            if '.' in v:
                v = v.split('.')[0]
            return '{0}{1}'.format(d, v)
        elif self._name == 'sles':
            v = self._version
            if '.' in v:
                v = v.split('.')
                v = v[0] + '-sp' + v[1]
            # else: TODO(rck): actually I don't know how non SPx looks like
            # in the repo it is just like "sles12"
            return '{0}{1}'.format(self._name, v)
        elif self._name == 'rhcos':
            vs = {
                '4.1': '8.0',
                '4.3': '8.1'
            }
            return 'rhel{0}'.format(vs.get(self._version, '8.1'))
        else:
            raise Exception("Could not determine repository information")


if __name__ == "__main__":
    import sys
    osreleasepath = os.environ.get('LB_OSRELEASE', '/etc/os-release')
    if len(sys.argv) == 2:
        osreleasepath = sys.argv[1]

    d = LinbitDistribution(osreleasepath)
    print('{0},{1},{2},{3}'.format(d.repo_name, d.name, d.version, d.family))
