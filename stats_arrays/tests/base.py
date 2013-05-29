import unittest
from numpy import *
from ..distributions import *
from scipy.special import erf
from ..errors import ImproperBoundsError, \
    UndefinedDistributionError, InvalidParamsError, UnreasonableBoundsError
from nose.plugins.skip import SkipTest
import numpy as np


class UncertaintyTestCase(unittest.TestCase):
    def make_params_array(self, length=1):
        assert isinstance(length, int)
        params = zeros((length,), dtype=[('input', 'u4'), ('output', 'u4'),
            ('loc', 'f4'), ('negative', 'b1'), ('scale', 'f4'),
            ('minimum', 'f4'), ('maximum', 'f4')])
        params['minimum'] = params['maximum'] = params['scale'] = NaN
        return params

    def seeded_random(self, seed=111111):
        return random.RandomState(seed)

    def biased_params_1d(self):
        oneDparams = self.make_params_array(1)
        oneDparams['minimum'] = 1
        oneDparams['loc'] = 3
        oneDparams['maximum'] = 4
        return oneDparams

    def biased_params_2d(self):
        params = self.make_params_array(2)
        params['minimum'] = 1
        params['loc'] = 3
        params['maximum'] = 4
        return params

    def test_uncertainty_base_validate(self):
        """UncertaintyBase: Mean exists, and bounds are ok if present."""
        params = self.make_params_array(1)
        params['maximum'] = 2
        params['loc'] = 1.6
        # Minimum too big
        params['minimum'] = 1.8
        self.assertRaises(ImproperBoundsError, UncertaintyBase.validate,
            params)
        # Mean above max
        params['minimum'] = 1
        params['loc'] = 2.5
        self.assertRaises(ImproperBoundsError, UncertaintyBase.validate,
            params)
        # Mean below min
        params['loc'] = 0.5
        self.assertRaises(ImproperBoundsError, UncertaintyBase.validate,
            params)
        # No mean
        params['loc'] = NaN
        self.assertRaises(InvalidParamsError, UncertaintyBase.validate,
            params)

    # def test_random_timing(self):
    #     import time
    #     t = time.time()
    #     params = self.make_params_array(1)
    #     params['loc'] = 1
    #     params['scale'] = 1
    #     sample = NormalUncertainty.random_variables(params, size=50000)
    #     print "Without limits: %.4f" % (time.time() - t)
    #     t = time.time()
    #     params = self.make_params_array(1)
    #     params['loc'] = 1
    #     params['scale'] = 1
    #     sample = NormalUncertainty.bounded_random_variables(params, size=50000)
    #     print "Without limits, but with bounded_r_v: %.4f" % (time.time() - t)
    #     t = time.time()
    #     params = self.make_params_array(1)
    #     params['maximum'] = -0.2
    #     params['loc'] = 1
    #     params['scale'] = 1
    #     sample = NormalUncertainty.bounded_random_variables(params, size=50000, maximum_iterations=1000)
    #     print "With limits: %.4f" % (time.time() - t)

    def test_check_2d_inputs(self):
        params = self.make_params_array(2)
        params['minimum'] = 0
        params['loc'] = 1
        params['maximum'] = 2
        # Params has 2 rows. The input vector can only have shape (2,) or (2, n)
        self.assertRaises(InvalidParamsError, UncertaintyBase.check_2d_inputs,
            params, array((1,)))
        self.assertRaises(InvalidParamsError, UncertaintyBase.check_2d_inputs,
            params, array(((1, 2),)))
        self.assertRaises(InvalidParamsError, UncertaintyBase.check_2d_inputs,
            params, array(((1, 2), (3, 4), (5, 6))))
        # Test 1-d input
        vector = UncertaintyBase.check_2d_inputs(params, array((1, 2)))
        self.assertTrue(allclose(vector, array(([1], [2]))))
        # Test 1-row 2-d input
        vector = UncertaintyBase.check_2d_inputs(params, array(((1, 2, 3),
            (1, 2, 3))))
        self.assertTrue(allclose(vector, array(((1, 2, 3), (1, 2, 3)))))

    @SkipTest
    def test_check_bounds_reasonableness(self):
        params = self.make_params_array(1)
        params['maximum'] = -0.3
        params['loc'] = 1
        params['scale'] = 1
        self.assertRaises(UnreasonableBoundsError,
            NormalUncertainty.check_bounds_reasonableness, params)

    def test_bounded_random_variables(self):
        params = self.make_params_array(1)
        params['maximum'] = -0.2 # Only ~ 10 percent of distribution
        params['loc'] = 1
        params['scale'] = 1
        sample = NormalUncertainty.bounded_random_variables(params, size=50000,
            maximum_iterations=1000)
        self.assertEqual((sample > -0.2).sum(), 0)
        self.assertEqual(sample.shape, (1, 50000))
        self.assertTrue(abs(sample.sum()) > 0)

    def test_bounded_uncertainty_base_validate(self):
        """BoundedUncertaintyBase: Make sure legitimate bounds are provided"""
        params = self.make_params_array(1)
        # Only maximum
        params['maximum'] = 1
        params['minimum'] = NaN
        self.assertRaises(ImproperBoundsError, BoundedUncertaintyBase.validate,
            params)
        # Only minimum
        params['maximum'] = NaN
        params['minimum'] = -1
        self.assertRaises(ImproperBoundsError, BoundedUncertaintyBase.validate,
            params)

    def test_undefined_uncertainty(self):
        params = self.make_params_array(1)
        self.assertRaises(UndefinedDistributionError, UndefinedUncertainty.cdf,
            params, random.random(10))
        params = self.make_params_array(2)
        params['loc'] = 9
        self.assertTrue(allclose(ones((2,3))*9,
            UndefinedUncertainty.random_variables(params, 3)))
        random_percentages = random.random(20).reshape(2, 10)
        self.assertTrue(allclose(ones((2,10))*9,
            UndefinedUncertainty.ppf(params, random_percentages)))
