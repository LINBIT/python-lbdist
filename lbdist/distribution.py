#!/usr/bin/env python
import os
import re
import subprocess
import platform
from functools import reduce

try:
    from urllib2 import urlopen
    from urllib2 import Request
except ImportError:
    from urllib.request import urlopen
    from urllib.request import Request


class Distribution(object):
    _pveversion = '/usr/bin/pveversion'

    def __init__(self, osreleasepath='/etc/os-release'):
        self._supported_dist_IDs = ('amzn', 'centos', 'rhel', 'rhcos', 'almalinux', 'rocky', 'debian',
                                    'ubuntu', 'xenenterprise', 'ol', 'sles', 'opensuse-leap', 'proxmox')
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
        if os.path.exists(Distribution._pveversion):
            osrelease['ID'] = 'proxmox'
            osrelease['ID_LIKE'] = 'debian'
        elif os.path.exists(self._osreleasepath):
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
            elif osrelease.get('ID', '') == 'opensuse-leap':  # they have ID_LIKE="suse opensuse"
                osrelease['ID_LIKE'] = 'sles'

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
                msg = 'No "VERSION" in your Debian {0}, are you running testing/sid?'.format(self._osreleasepath)
                raise Exception(msg)

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
            # and again in the middle of the 8 series (removed '(Core|Final)')
            m = re.search(r'^CentOS .* ([\d.]+)', line)
            if not m:
                raise Exception('Could not determine version information for your Centos')
            version = m.group(1)
        elif self._name == 'amzn':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'almalinux':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'rocky':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'rhel':
            try:
                version = self._osrelease['VERSION_ID']
            except KeyError:
                line = ''
                with open('/etc/redhat-release') as cr:
                    line = cr.readline().strip()
                m = re.search(r'^Red Hat Enterprise .* ([\d.]+) \(.*\)$', line)
                if not m:
                    raise Exception('Could not determine version information for your RHEL6')
                version = m.group(1)
        elif self._name == 'rhcos':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'xenenterprise':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'ol':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'sles' or self._name == 'opensuse-leap':
            version = self._osrelease['VERSION_ID']
        elif self._name == 'proxmox':
            version = subprocess.check_output([Distribution._pveversion]).decode().strip().split('/')[1]
            # this gave us something like 7.2-5, cut the '-' part
            version = version.split('-')[0]
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
    def __init__(self, osreleasepath='/etc/os-release'):
        super(LinbitDistribution, self).__init__(osreleasepath)

    @property
    def repo_name(self):
        # use '{0}' instead of '{}', RHEL 6 does not handle the modern version
        if self._name in ('debian', 'ubuntu'):
            return self._version
        elif self._name in ('rhel', 'centos', 'amzn', 'almalinux', 'rocky'):
            d = 'rhel'
            if self._name == 'amzn':
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
        elif self._name == 'sles' or self._name == 'opensuse-leap':
            v = self._version
            if '.' in v:
                v = v.split('.')
                v = v[0] + '-sp' + v[1]
            # else: TODO(rck): actually I don't know how non SPx looks like
            # in the repo it is just like "sles12"
            return 'sles{0}'.format(v)
        elif self._name == 'proxmox':
            v = self._version
            if '.' in v:
                v = v.split('.')
                v = v[0]
            return 'proxmox-{0}'.format(v)
        elif self._name == 'rhcos':
            osrel_ver = self.osrelease.get('RHEL_VERSION')
            vs = {
                '4.1': '8.0',
                '4.2': '8.0',
                '4.3': '8.1',
                '4.4': '8.1',
                '4.5': '8.2',
                '4.6': '8.2',
                '4.7': '8.3',
            }
            return 'rhel{0}'.format(vs.get(self._version) or osrel_ver or '8.6')
        else:
            raise Exception("Could not determine repository information")

    def epilogue(self, with_pacemaker=False):
        pkgs = """Looks like you executed the script on a {0} system
You might want to install the following packages on this node:
  {1}"""

        # we want to support old Python, "which" is easy enough
        def is_in_path(executable):
            path = os.getenv('PATH')
            if not path:
                return False
            for p in path.split(os.path.pathsep):
                p = os.path.join(p, executable)
                if os.path.exists(p) and os.access(p, os.X_OK):
                    return True
            return False

        def get_install_tool():
            # make sure to order by preference
            if is_in_path('apt'):
                return 'apt install'
            if is_in_path('apt-get'):
                return 'apt-get install'
            if is_in_path('zypper'):
                return 'zypper install'
            if is_in_path('dnf'):
                return 'dnf install'
            if is_in_path('yum'):
                return 'yum install'
            return '<your package manager install>'

        def get_best_module():
            uname_r = os.uname()[2]
            if self._family == 'debian':
                return 'drbd-module-{0} # or drbd-dkms'.format(uname_r)
            # something bestkernelmodule should be able to handle
            # it is fine if this is something bestkernelmodule does not handle,
            # it will raise an exception and we return the default kmod-drbd
            os_release = open(self._osreleasepath)
            data = os_release.read()
            os_release.close()
            # TODO: give it a dedicated subdomain with standard port
            req = Request('http://drbd.io:3030/api/v1/best/'+uname_r, data=data.encode(), method='POST')
            try:
                resp = urlopen(req, timeout=5)
                best = resp.read().decode()
                # returns a file name including .rpm, split that off
                # pkgmanagers like dnf don't like extensions/look for local files,...
                return os.path.splitext(best)[0]
            except Exception:
                # sles or rhel alike:
                kmod = '<no default kernel module for your distribution>'
                if self._family == 'rhel':
                    kmod = 'kmod-drbd'
                elif self._family == 'sles':
                    kmod = 'drbd-kmp'
                return kmod

        def add_controller_satellite(tool):
            return '\nIf this is a SDS controller node you might want to install:\n' \
                   '  {0} linbit-sds-controller\n' \
                   'You can configure a highly-available controller later via:\n' \
                   '  https://linbit.com/drbd-user-guide/linstor-guide-1_0-en/#s-linstor_ha\n' \
                   'If this is a SDS satellite node you might want to install:\n' \
                   '  {1} linbit-sds-satellite\n'.format(tool, tool)

        def add_pacemaker(tool):
            return '\nIf you intend to use Pacemaker you might want to install:\n' \
                   '  {0} pacemaker corosync\n'.format(tool)

        install_tool = get_install_tool()
        best_module = get_best_module()
        utils = ''
        if self._family == 'debian':
            utils = 'drbd-utils'
        elif self._family == 'sles' or self._family == 'rhel':
            utils = 'drbd-utils drbd-udev'

        dist = 'GENERIC'
        doc = 'https://linbit.com/drbd-user-guide/linstor-guide-1_0-en/#p-administration'
        if is_in_path('oned'):
            dist = 'OpenNebula frontend'
            utils += ' linstor-opennebula'
            doc = 'https://linbit.com/drbd-user-guide/linstor-guide-1_0-en/#ch-opennebula-linstor'
        elif self._name == 'proxmox':
            dist = 'PVE'
            best_module = 'drbd-dkms'
            utils += ' linstor-proxmox'
            doc = 'https://linbit.com/drbd-user-guide/linstor-guide-1_0-en/#ch-proxmox-linstor'

        # keep best_module at last position, it might contain a comment section (foo # bar)
        txt = pkgs.format(dist, install_tool + ' ' + utils + ' ' + best_module)
        txt += add_controller_satellite(install_tool)
        if with_pacemaker:
            txt += add_pacemaker(install_tool)
        txt += '\nFor documentation see:\n  ' + doc
        return txt

    @classmethod
    def best_drbd_kmod(cls, choices, osreleasepath='/etc/os-release', name=None, hostkernel=None):
        # choices should be kernel module packages, they are allowed to have a path prefix
        # the best matching one, or None is returned
        if not name:
            name = cls(osreleasepath)._name

        # keep as startswith, which allows forcing rhel by setting the family as name
        if not (name.startswith('rhel') or name.startswith('centos') or
                name.startswith('almalinux') or name.startswith('rocky') or
                name.startswith('sles')):
            return None

        if not hostkernel:
            hostkernel = platform.uname()[2]
        hostkernelsplit = hostkernel.replace('-', '.')
        hostkernelsplit = hostkernelsplit.split('.')[::-1]
        # strip x86, -default,... from the end
        for i, e in enumerate(hostkernelsplit):
            if e.isdigit():
                hostkernelsplit = hostkernelsplit[i:][::-1]
                break

        kmap = {}
        for c in choices:
            kpart = os.path.basename(c)
            if not (kpart.startswith('kmod-drbd') or kpart.startswith('drbd-kmp')):
                continue
            kpart = '_'.join(kpart.split('_')[1:])  # strip kmod-drbd-x.y.z_ prefix
            if name.startswith('sles') and kpart[0] == 'k':  # strip k from k4.12.14_197.29-1
                kpart = kpart[1:]

            kpart = kpart.split('-')[0]  # strip revision and everything past it
            # convert the '_' in 3.10.0_1062,
            # but only the first one as in 4.18.0_80.1.2.el8_0.x86_64
            kpart = kpart.replace('_', '.', 1)

            kps = kpart.split('.')
            # the weird stuff should now be at the end of the array (arch, el*)
            kps = list(filter(lambda a: a.isdigit(), kps))
            if len(kps) < 3:  # first 3 are the kernel
                continue
            valid = True

            for i in range(3):
                if hostkernelsplit[i] != kps[i]:
                    valid = False
                    break
            if not valid:
                continue

            kmap['.'.join(kps[3:])] = c

        hostkernelsplit = hostkernelsplit[3:]

        def kcmp(v1, v2):
            v1s, v2s = v1.split('.'), v2.split('.')
            hks = hostkernelsplit

            ml = max(len(hks), len(v1s), len(v2s))
            for lst in (v1s, v2s, hks):
                lst += [0]*(ml-len(lst))

            for i, e in enumerate(hks):
                e = int(e)
                d1 = e - int(v1s[i])
                d2 = e - int(v2s[i])
                if d1 == d2:
                    continue
                # smaller positive one
                if d1 >= 0 and d2 >= 0:
                    if d1 < d2:
                        return v1
                    else:
                        return v2
                elif d1 >= 0 and d2 < 0:
                    return v1
                elif d1 < 0 and d2 >= 0:
                    return v2
                else:  # both negative and therefore higher
                    if d1 < d2:
                        return v2
                    else:
                        return v1

            # no winner as there was no early return
            return v1

        keys = kmap.keys()
        if not keys:
            return None
        return kmap[reduce(kcmp, keys)]


if __name__ == "__main__":
    import sys
    osreleasepath = os.environ.get('LB_OSRELEASE', '/etc/os-release')
    if len(sys.argv) == 2:
        osreleasepath = sys.argv[1]

    d = LinbitDistribution(osreleasepath)
    print('{0},{1},{2},{3}'.format(d.repo_name, d.name, d.version, d.family))
