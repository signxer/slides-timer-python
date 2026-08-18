#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides-timer 核心单元测试（不依赖 GUI 窗口）。

运行：
  python3 test/test_core.py
  QT_QPA_PLATFORM=offscreen python3 -m pytest test/  # GUI 测试见 test_gui.py
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from config import cfg, ConfigManager, DEFAULT_CONFIG


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mktemp(suffix='.json')
        self._orig_file = __import__('config').CONFIG_FILE
        import config as cfgmod
        cfgmod.CONFIG_FILE = self.tmp
        # fresh instance
        self.mgr = ConfigManager()

    def tearDown(self):
        import config as cfgmod
        cfgmod.CONFIG_FILE = self._orig_file
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_defaults(self):
        self.assertEqual(self.mgr.get("font_size"), 24)
        self.assertEqual(self.mgr.get("position"), "top")
        self.assertEqual(self.mgr.get("warning_trigger_type"), "percent")

    def test_set_and_get(self):
        self.mgr.set("font_size", 48)
        self.assertEqual(self.mgr.get("font_size"), 48)

    def test_get_unknown_key(self):
        self.assertIsNone(self.mgr.get("nonexistent_key"))

    def test_persist_to_disk(self):
        self.mgr.set("text_warning", "测试提示")
        # new instance should read it back
        mgr2 = ConfigManager()
        self.assertEqual(mgr2.get("text_warning"), "测试提示")

    def test_bad_json_uses_defaults(self):
        with open(self.tmp, 'w') as f:
            f.write("not json")
        mgr = ConfigManager()
        self.assertEqual(mgr.get("font_size"), 24)

    def test_ppt_timers_empty_by_default(self):
        self.assertEqual(self.mgr.get("ppt_timers"), {})


if __name__ == '__main__':
    unittest.main(verbosity=2)