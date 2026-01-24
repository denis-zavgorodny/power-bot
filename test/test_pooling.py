import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from bot.pooling import load_electricity_state, save_electricity_state, pooling_status, STATE_FILE


class TestLoadElectricityState(unittest.TestCase):
    """Test cases for load_electricity_state() function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_state_file = os.path.join(self.test_dir, "electricity_state.json")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    @patch('bot.pooling.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"isElectricityAvailable": true}')
    def test_load_state_when_file_exists_and_has_true(self, mock_file, mock_exists):
        """Test loading state when file exists and contains True."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = True
            
            result = load_electricity_state()
            
            self.assertTrue(result)
            mock_exists.assert_called_once_with(self.test_state_file)
            mock_file.assert_called_once_with(self.test_state_file, 'r')

    @patch('bot.pooling.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"isElectricityAvailable": false}')
    def test_load_state_when_file_exists_and_has_false(self, mock_file, mock_exists):
        """Test loading state when file exists and contains False."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = True
            
            result = load_electricity_state()
            
            self.assertFalse(result)

    @patch('bot.pooling.os.path.exists')
    def test_load_state_when_file_does_not_exist(self, mock_exists):
        """Test loading state when file does not exist."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = False
            
            result = load_electricity_state()
            
            self.assertIsNone(result)
            mock_exists.assert_called_once_with(self.test_state_file)

    @patch('bot.pooling.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": "data"}')
    def test_load_state_when_file_has_invalid_key(self, mock_file, mock_exists):
        """Test loading state when file exists but has invalid key."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = True
            
            result = load_electricity_state()
            
            self.assertIsNone(result)

    @patch('bot.pooling.os.path.exists')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_load_state_when_file_read_fails(self, mock_file, mock_exists):
        """Test loading state when file read fails."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = True
            
            result = load_electricity_state()
            
            self.assertIsNone(result)

    @patch('bot.pooling.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_state_when_file_has_invalid_json(self, mock_file, mock_exists):
        """Test loading state when file contains invalid JSON."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            mock_exists.return_value = True
            
            result = load_electricity_state()
            
            self.assertIsNone(result)


class TestSaveElectricityState(unittest.TestCase):
    """Test cases for save_electricity_state() function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_state_file = os.path.join(self.test_dir, "electricity_state.json")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    @patch('bot.pooling.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('bot.pooling.json.dump')
    def test_save_state_true(self, mock_json_dump, mock_file, mock_makedirs):
        """Test saving state as True."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            save_electricity_state(True)
            
            mock_makedirs.assert_called_once_with(os.path.dirname(self.test_state_file), exist_ok=True)
            mock_file.assert_called_once_with(self.test_state_file, 'w')
            mock_json_dump.assert_called_once_with({"isElectricityAvailable": True}, mock_file.return_value.__enter__.return_value)

    @patch('bot.pooling.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('bot.pooling.json.dump')
    def test_save_state_false(self, mock_json_dump, mock_file, mock_makedirs):
        """Test saving state as False."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            save_electricity_state(False)
            
            mock_json_dump.assert_called_once_with({"isElectricityAvailable": False}, mock_file.return_value.__enter__.return_value)

    @patch('bot.pooling.os.makedirs', side_effect=OSError("Permission denied"))
    def test_save_state_when_directory_creation_fails(self, mock_makedirs):
        """Test saving state when directory creation fails."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            # Should not raise exception, just log error
            try:
                save_electricity_state(True)
            except Exception:
                self.fail("save_electricity_state() should handle errors gracefully")

    @patch('bot.pooling.os.makedirs')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_state_when_file_write_fails(self, mock_file, mock_makedirs):
        """Test saving state when file write fails."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            # Should not raise exception, just log error
            try:
                save_electricity_state(True)
            except Exception:
                self.fail("save_electricity_state() should handle errors gracefully")


class TestPoolingStatusWithPersistence(unittest.TestCase):
    """Test cases for pooling_status() function with state persistence."""

    @patch('bot.pooling.save_electricity_state')
    @patch('bot.pooling.load_electricity_state')
    @patch('bot.pooling.requests_session_with_retries')
    @patch('bot.pooling.time.sleep')
    def test_pooling_status_loads_state_on_startup(self, mock_sleep, mock_session_factory, mock_load, mock_save):
        """Test that pooling_status loads state from file on startup."""
        mock_load.return_value = False
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"has_electricity": True}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session
        mock_sleep.side_effect = KeyboardInterrupt()  # Stop the infinite loop
        
        callback = MagicMock()
        
        try:
            pooling_status("http://test.endpoint", callback, interval=1)
        except KeyboardInterrupt:
            pass
        
        mock_load.assert_called_once()

    @patch('bot.pooling.save_electricity_state')
    @patch('bot.pooling.load_electricity_state')
    @patch('bot.pooling.requests_session_with_retries')
    @patch('bot.pooling.time.sleep')
    def test_pooling_status_saves_state_when_changes_to_true(self, mock_sleep, mock_session_factory, mock_load, mock_save):
        """Test that pooling_status saves state when it changes to True."""
        mock_load.return_value = False  # Initial state is False
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"has_electricity": True}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session
        mock_sleep.side_effect = KeyboardInterrupt()  # Stop after first iteration
        
        callback = MagicMock()
        
        try:
            pooling_status("http://test.endpoint", callback, interval=1)
        except KeyboardInterrupt:
            pass
        
        # Should save True when state changes
        mock_save.assert_called_with(True)
        callback.assert_called_once_with(True)

    @patch('bot.pooling.save_electricity_state')
    @patch('bot.pooling.load_electricity_state')
    @patch('bot.pooling.requests_session_with_retries')
    @patch('bot.pooling.time.sleep')
    def test_pooling_status_saves_state_when_changes_to_false(self, mock_sleep, mock_session_factory, mock_load, mock_save):
        """Test that pooling_status saves state when it changes to False."""
        mock_load.return_value = True  # Initial state is True
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"has_electricity": False}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session
        mock_sleep.side_effect = KeyboardInterrupt()  # Stop after first iteration
        
        callback = MagicMock()
        
        try:
            pooling_status("http://test.endpoint", callback, interval=1)
        except KeyboardInterrupt:
            pass
        
        # Should save False when state changes
        mock_save.assert_called_with(False)
        callback.assert_called_once_with(False)

    @patch('bot.pooling.save_electricity_state')
    @patch('bot.pooling.load_electricity_state')
    @patch('bot.pooling.requests_session_with_retries')
    @patch('bot.pooling.time.sleep')
    def test_pooling_status_saves_state_when_stays_true(self, mock_sleep, mock_session_factory, mock_load, mock_save):
        """Test that pooling_status saves state even when it stays True."""
        mock_load.return_value = True  # Initial state is True
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"has_electricity": True}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session
        mock_sleep.side_effect = KeyboardInterrupt()  # Stop after first iteration
        
        callback = MagicMock()
        
        try:
            pooling_status("http://test.endpoint", callback, interval=1)
        except KeyboardInterrupt:
            pass
        
        # Should save True even if state doesn't change
        mock_save.assert_called_with(True)
        # Should not call callback when state doesn't change
        callback.assert_not_called()

    @patch('bot.pooling.save_electricity_state')
    @patch('bot.pooling.load_electricity_state')
    @patch('bot.pooling.requests_session_with_retries')
    @patch('bot.pooling.time.sleep')
    def test_pooling_status_handles_none_initial_state(self, mock_sleep, mock_session_factory, mock_load, mock_save):
        """Test that pooling_status handles None initial state correctly."""
        mock_load.return_value = None  # No previous state
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"has_electricity": True}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_factory.return_value = mock_session
        mock_sleep.side_effect = KeyboardInterrupt()  # Stop after first iteration
        
        callback = MagicMock()
        
        try:
            pooling_status("http://test.endpoint", callback, interval=1)
        except KeyboardInterrupt:
            pass
        
        # Should save True
        mock_save.assert_called_with(True)
        # Should not call callback when transitioning from None
        callback.assert_not_called()


class TestElectricityStatePersistenceIntegration(unittest.TestCase):
    """Integration tests using real file operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_state_file = os.path.join(self.test_dir, "electricity_state.json")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_save_and_load_cycle_true(self):
        """Test that we can save True and load it back."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            # Save True
            save_electricity_state(True)
            
            # Verify file was created
            self.assertTrue(os.path.exists(self.test_state_file))
            
            # Load it back
            result = load_electricity_state()
            
            # Should be True
            self.assertTrue(result)

    def test_save_and_load_cycle_false(self):
        """Test that we can save False and load it back."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            # Save False
            save_electricity_state(False)
            
            # Verify file was created
            self.assertTrue(os.path.exists(self.test_state_file))
            
            # Load it back
            result = load_electricity_state()
            
            # Should be False
            self.assertFalse(result)

    def test_save_and_load_cycle_state_change(self):
        """Test that state changes are properly persisted."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            # Save True
            save_electricity_state(True)
            self.assertTrue(load_electricity_state())
            
            # Change to False
            save_electricity_state(False)
            self.assertFalse(load_electricity_state())
            
            # Change back to True
            save_electricity_state(True)
            self.assertTrue(load_electricity_state())

    def test_file_content_format(self):
        """Test that the file contains properly formatted JSON."""
        with patch('bot.pooling.STATE_FILE', self.test_state_file):
            save_electricity_state(True)
            
            # Read file directly
            with open(self.test_state_file, 'r') as f:
                data = json.load(f)
            
            # Verify structure
            self.assertIn("isElectricityAvailable", data)
            self.assertTrue(data["isElectricityAvailable"])


if __name__ == '__main__':
    unittest.main()
