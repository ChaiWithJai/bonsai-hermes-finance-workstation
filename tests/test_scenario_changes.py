import unittest
from finance_workstation.tools import execute, scenario_changes


class ScenarioChangeTests(unittest.TestCase):
    def test_demo_downside_change_is_220_basis_points(self):
        report = execute('compare_scenarios', {})
        self.assertEqual(report['candidate_minus_current']['base'],
                         {'percentage_points': .9, 'basis_points': 90.0})
        self.assertEqual(report['candidate_minus_current']['downside'],
                         {'percentage_points': -2.2, 'basis_points': -220.0})

    def test_preserves_units_sign_and_zero_for_other_values(self):
        result = scenario_changes({'base': 1.25, 'upside': 3.5, 'downside': -4},
                                  {'base': 1.24, 'upside': 3.5, 'downside': -3.75})
        self.assertEqual(result, {
            'base': {'percentage_points': -.01, 'basis_points': -1.0},
            'upside': {'percentage_points': 0.0, 'basis_points': 0.0},
            'downside': {'percentage_points': .25, 'basis_points': 25.0}})
