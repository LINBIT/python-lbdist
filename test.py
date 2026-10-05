#!/usr/bin/env python

import os
import tempfile
import unittest
from lbdist.distribution import LinbitDistribution


class TestBestKernel(unittest.TestCase):
    def test_numbers_only(self):
        b = LinbitDistribution.best_drbd_kmod(['kmod-drbd-9.0.25_4.18.0_80.1.2.el8_0.x86_64-1',
                                               'kmod-drbd-9.0.25_4.18.0_80.el8.s390x-1'],
                                              name='centos', hostkernel='4.18.0')
        self.assertEqual(b, 'kmod-drbd-9.0.25_4.18.0_80.el8.s390x-1')

    def test_sles(self):
        b = LinbitDistribution.best_drbd_kmod(['sles15-sp0/amd64/drbd-kmp-default-9.0.24_k4.12.14_25.25-1.x86_64.rpm',
                                               'sles15-sp1/amd64/drbd-kmp-default-9.0.24_k4.12.14_197.44-1.x86_64.rpm',
                                               'sles15-sp1/amd64/drbd-kmp-default-9.0.24_k4.12.14_197.29-1.x86_64.rpm'],
                                              name='sles15-sp1', hostkernel='4.12.14.25')
        self.assertEqual(b, 'sles15-sp0/amd64/drbd-kmp-default-9.0.24_k4.12.14_25.25-1.x86_64.rpm')


class TestRepoName(unittest.TestCase):
    def repo_name(self, osid, version_id):
        with tempfile.NamedTemporaryFile('w', suffix='os-release', delete=False) as f:
            f.write('ID="{0}"\nVERSION_ID="{1}"\n'.format(osid, version_id))
        try:
            return LinbitDistribution(f.name).repo_name
        finally:
            os.unlink(f.name)

    def test_sles_service_packs(self):
        self.assertEqual(self.repo_name('sles', '12.5'), 'sles12-sp5')
        self.assertEqual(self.repo_name('sles', '15'), 'sles15')
        self.assertEqual(self.repo_name('sles', '15.7'), 'sles15-sp7')
        self.assertEqual(self.repo_name('opensuse-leap', '15.6'), 'sles15-sp6')

    def test_sles_minor_releases(self):
        self.assertEqual(self.repo_name('sles', '16.0'), 'sles16.0')
        self.assertEqual(self.repo_name('sles', '16.1'), 'sles16.1')
        self.assertEqual(self.repo_name('opensuse-leap', '16.0'), 'sles16.0')


if __name__ == '__main__':
    unittest.main()
