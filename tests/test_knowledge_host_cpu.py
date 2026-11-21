#!/usr/bin/env python3
"""Act 32: whole-host CPU busy upper-bound, no fake office attribution."""
import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "government/knowledge-budget-tool.py"
spec = importlib.util.spec_from_file_location("knowledge_budget_tool", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample(seconds, boot="12345678-1234-1234-1234-123456789abc",
           source="proc-stat-host-busy-upper-bound-v1"):
    return {"cpu_seconds": seconds, "cpu_boot_id": boot,
            "cpu_available": True, "cpu_source": source,
            "cpu_attribution": "conservative-whole-host-upper-bound",
            "session_found": True, "tokens": {"total": 80}}


class CpuUpperBound(unittest.TestCase):
    def test_real_monotone_host_observations(self):
        a = mod.host_cpu()
        b = mod.host_cpu()
        self.assertTrue(a["cpu_available"])
        self.assertEqual(a["cpu_boot_id"], b["cpu_boot_id"])
        self.assertGreaterEqual(b["cpu_seconds"], a["cpu_seconds"])
        self.assertEqual(a["cpu_source"], "proc-stat-host-busy-upper-bound-v1")
        actual = subprocess.check_output(
            [sys.executable, str(TOOL), "cpu-meter"], text=True)
        self.assertIn("conservative-whole-host-upper-bound", actual)

    def test_delta_and_provenance(self):
        baseline = sample(1_000_000)
        current = sample(1_000_054)
        delta = mod.cpu_delta(baseline, current)
        self.assertEqual(delta["cpu_seconds"], 54)
        self.assertEqual(delta["cpu_host_seconds"], 1_000_054)
        self.assertTrue(delta["cpu_upper_bound"])
        self.assertEqual(delta["tokens"]["total"], 80)
        later = mod.cpu_delta(baseline, sample(1_000_080), delta)
        self.assertEqual(later["cpu_seconds"], 80)

    def test_fail_closed_on_reboot_and_counter_reset(self):
        baseline = sample(1_000_000)
        with self.assertRaisesRegex(ValueError, "reboot"):
            mod.cpu_delta(baseline, sample(200, "87654321-1234-1234-1234-123456789abc"))
        with self.assertRaisesRegex(ValueError, "reset"):
            mod.cpu_delta(baseline, sample(999_999))
        with self.assertRaisesRegex(ValueError, "source changed"):
            mod.cpu_delta(baseline, sample(1_000_050, source="runner-pid"))
        previous = mod.cpu_delta(baseline, sample(1_000_050))
        with self.assertRaisesRegex(ValueError, "regressed"):
            mod.cpu_delta(baseline, sample(1_000_049), previous)
        with self.assertRaisesRegex(ValueError, "previous CPU meter"):
            mod.cpu_delta(baseline, sample(1_000_060),
                          {"cpu_boot_id": "other", "cpu_host_seconds": 1_000_051})

    def test_absolute_cpu_not_used_for_caps(self):
        caps = {"tokens_total": 400_000, "cpu_seconds": 90,
                "wall_seconds": 3600}
        baseline = sample(2_500_000)
        adjusted = mod.cpu_delta(baseline, sample(2_500_055))
        result = mod.overrun(caps, adjusted, 40)
        self.assertFalse(result["over"])
        more = mod.cpu_delta(baseline, sample(2_500_091), adjusted)
        result = mod.overrun(caps, more, 65)
        self.assertTrue(result["over"])
        self.assertIn("cpu_seconds", result["reasons"])

    def test_config_describes_bound_not_fake_peroffice_cpu(self):
        config = mod.load_config(str(ROOT / "government/knowledge-budget.conf"))[0]
        self.assertFalse(mod.validate_config(config))
        config["cpu_meter"]["attribution"] = "measured-per-office"
        self.assertTrue(mod.validate_config(config))

if __name__ == "__main__":
    unittest.main()
