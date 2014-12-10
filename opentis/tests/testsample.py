'''
@author: David W.H. Swenson
'''

import os
import numpy as np

from nose.tools import (assert_equal, assert_not_equal, assert_items_equal,
                        assert_almost_equal, raises)
from nose.plugins.skip import Skip, SkipTest
from test_helpers import true_func, assert_equal_array_array

from opentis.sample import *
from opentis.trajectory import Trajectory, Sample

from opentis.ensemble import LengthEnsemble

class testSampleSet(object):
    def setup(self):
        self.ensA = LengthEnsemble(1)
        self.ensB = LengthEnsemble(2)
        traj0A = Trajectory([0.5])
        traj1A = Trajectory([1.0])
        traj2B = Trajectory([0.5, 0.75])
        traj2B_ = Trajectory([0.8, 0.9])
        self.s0A = Sample(replica=0, trajectory=traj0A, ensemble=self.ensA)
        self.s1A = Sample(replica=1, trajectory=traj1A, ensemble=self.ensA)
        self.s2B = Sample(replica=2, trajectory=traj2B, ensemble=self.ensB)
        self.s2B_ = Sample(replica=2, trajectory=traj2B_, ensemble=self.ensB)
        self.testset = SampleSet([self.s0A, self.s1A, self.s2B])

    def test_initialization(self):
        self.testset.consistency_check()

    def test_iter(self):
        samps = [self.s0A, self.s1A, self.s2B]
        for samp in self.testset:
            assert_equal(samp in samps, True)

    def test_contains(self):
        samps = [self.s0A, self.s1A, self.s2B]
        for samp in samps:
            assert_equal(samp in self.testset, True)

    def test_len(self):
        assert_equal(len(self.testset), 3)

    def test_getitem_ensemble(self):
        assert_equal(self.testset[self.ensB], self.s2B)
        # TODO: add test that we pick at random for ensA

    def test_getitem_replica(self):
        assert_equal(self.testset[0], self.s0A)
        assert_equal(self.testset[1], self.s1A)
        assert_equal(self.testset[2], self.s2B)
        # TODO: add test that we pick at random

    def test_setitem_ensemble(self):
        ensC = LengthEnsemble(3)
        traj3C = Trajectory([-0.5, -0.25, 0.1])
        s3C = Sample(replica=3, trajectory=traj3C, ensemble=ensC)
        self.testset[ensC] = s3C
        self.testset.consistency_check()
        assert_equal(len(self.testset), 4)

    def test_setitem_replace_ensemble(self):
        self.testset[self.ensB] = self.s2B_
        assert_equal(self.s2B in self.testset, False)
        assert_equal(self.s2B_ in self.testset, True)
        assert_equal(self.testset[2], self.s2B_)
        assert_equal(self.testset[self.ensB], self.s2B_)
        # TODO add test that we replace at random

    def test_setitem_replica(self):
        ensC = LengthEnsemble(3)
        traj3C = Trajectory([-0.5, -0.25, 0.1])
        s3C = Sample(replica=3, trajectory=traj3C, ensemble=ensC)
        self.testset[3] = s3C
        self.testset.consistency_check()
        assert_equal(len(self.testset), 4)

    def test_setitem_replace_replica(self):
        self.testset[2] = self.s2B_
        assert_equal(self.s2B in self.testset, False)
        assert_equal(self.s2B_ in self.testset, True)
        assert_equal(self.testset[2], self.s2B_)
        # TODO add test that we replace at random

    def test_illegal_assign_ensemble(self):
        # if the key doesn't match the sample
        raise SkipTest

    def test_illegal_assign_replica(self):
        # if the key doesn't match the sample
        raise SkipTest

    def test_setitem_itemexists(self):
        # exact sample is already there
        raise SkipTest

    def test_additem(self):
        raise SkipTest

    def test_additem_itemexists(self):
        # exact sample is already there
        raise SkipTest

    def test_deleteitem(self):
        raise SkipTest

    def test_apply_samples(self):
        raise SkipTest

    def test_consistency_fail_size_ensdict(self):
        raise SkipTest

    def test_consistency_fail_size_repdict(self):
        raise SkipTest

    def test_consistency_fail_sample_in_ensdict(self):
        raise SkipTest

    def test_consistency_fail_sample_in_repdict(self):
        raise SkipTest
