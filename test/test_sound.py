#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides-timer - SoundPlayer 单元测试。
"""
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from sound_player import SoundPlayer
import sound_player


class TestSoundPlayer(unittest.TestCase):
    def test_play_empty_path(self):
        """空路径应静默跳过。"""
        SoundPlayer.play("")
        SoundPlayer.play(None)
        # 不抛异常就算通过

    def test_play_nonexistent_file(self):
        """不存在的文件应静默跳过。"""
        SoundPlayer.play("/nonexistent/file.wav")

    @mock.patch.object(sound_player.threading, 'Thread')
    def test_play_creates_daemon_thread(self, mock_thread):
        """play 应创建 daemon 线程调用 _play_sync。"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmpfile = f.name
        try:
            SoundPlayer.play(tmpfile)
            mock_thread.assert_called_once()
            _, kwargs = mock_thread.call_args
            self.assertTrue(kwargs.get('daemon', False), "线程应为 daemon")
            self.assertEqual(kwargs['args'], (tmpfile,))
        finally:
            os.unlink(tmpfile)

    def test_play_real_path_no_error(self):
        """play 实际调用不应抛异常（即使文件不存在也能静默处理）。"""
        SoundPlayer.play("/tmp/__nonexistent_test_file__.wav")

    def test_play_sync_linux_fallback(self):
        """_play_sync 在 Linux/macOS 上应尝试 afplay/aplay 等。"""
        with mock.patch('sys.platform', 'linux'):
            with mock.patch('subprocess.run') as m:
                m.side_effect = FileNotFoundError("no aplay")
                # 所有播放器均找不到 → 应静默返回，不抛异常
                SoundPlayer._play_sync("/some/file.wav")
                # 应尝试至少 2 个播放器
                self.assertGreater(m.call_count, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)