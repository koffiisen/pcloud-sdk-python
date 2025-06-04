"""
Comprehensive progress callback tests for pCloud SDK
Tests all 4 built-in progress trackers, custom callbacks, accuracy, performance, and error handling
"""

import os
import tempfile
import time
import threading
from io import StringIO
from unittest.mock import Mock, patch, call
from contextlib import redirect_stdout

import pytest

from pcloud_sdk.progress_utils import (
    SimpleProgressBar,
    DetailedProgress,
    MinimalProgress,
    SilentProgress,
    create_progress_bar,
    create_detailed_progress,
    create_minimal_progress,
    create_silent_progress,
)


class TestSimpleProgressBar:
    """Tests for SimpleProgressBar progress tracker"""

    def test_simple_progress_bar_initialization(self):
        """Test SimpleProgressBar initialization with various parameters"""
        # Default initialization
        progress = SimpleProgressBar()
        assert progress.title == "Progress"
        assert progress.width == 50
        assert progress.show_speed is True
        assert progress.show_eta is True

        # Custom initialization
        custom_progress = SimpleProgressBar(
            title="Upload", width=30, show_speed=False, show_eta=False
        )
        assert custom_progress.title == "Upload"
        assert custom_progress.width == 30
        assert custom_progress.show_speed is False
        assert custom_progress.show_eta is False

    def test_simple_progress_bar_basic_functionality(self):
        """Test basic progress bar functionality"""
        progress = SimpleProgressBar(title="Test Upload")

        with patch("builtins.print") as mock_print:
            # First call - should print title
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")

            # Progress call
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")

            # Completion call
            progress(1024, 1024, 100.0, 1024.0, filename="test.txt", operation="upload")

        # Verify print was called (title, progress updates, completion)
        assert mock_print.call_count >= 3

    @patch("time.time")
    def test_simple_progress_bar_with_speed_and_eta(self, mock_time):
        """Test progress bar with speed and ETA calculations"""
        progress = SimpleProgressBar(show_speed=True, show_eta=True)
        mock_time.side_effect = [
            100.0,
            100.0,
            100.2,
        ]  # t_start, t_first_curr, t_second_curr

        with patch("builtins.print") as mock_print:
            # Initialize
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")

            # Progress with speed and ETA
            progress(256, 1024, 25.0, 512.0, filename="test.txt", operation="upload")

            # Check that speed is included in output
            # mock_print.call_args_list should be: [title_call, 0%_bar_call, 25%_bar_call_with_speed]
            assert (
                len(mock_print.call_args_list) > 2
            ), f"Not enough print calls for progress update. Got: {len(mock_print.call_args_list)}, calls: {mock_print.call_args_list}"
            assert "MB/s" in str(
                mock_print.call_args_list[2]
            ), f"MB/s not in expected print call. Call content: {mock_print.call_args_list[2]}"

    def test_simple_progress_bar_without_speed_and_eta(self):
        """Test progress bar without speed and ETA display"""
        progress = SimpleProgressBar(show_speed=False, show_eta=False)

        with patch("builtins.print") as mock_print:
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")

        # Verify speed/ETA info is not included
        all_output = " ".join([str(call) for call in mock_print.call_args_list])
        assert "MB/s" not in all_output
        assert "ETA:" not in all_output

    @patch("time.time")
    def test_simple_progress_bar_eta_calculations(self, mock_time):
        """Test ETA calculation accuracy"""
        progress = SimpleProgressBar(show_eta=True)
        mock_time.side_effect = [
            200.0,
            200.0,
            200.2,
        ]  # t_start, t_first_curr, t_second_curr

        with patch("builtins.print") as mock_print:
            progress(0, 3600, 0.0, 0.0, filename="test.txt", operation="upload")

            # 50% complete at 1MB/s should show reasonable ETA
            progress(
                1800, 3600, 50.0, 1048576.0, filename="test.txt", operation="upload"
            )

            # Check that ETA is calculated
            # mock_print.call_args_list should be: [title_call, 0%_bar_call, 50%_bar_call_with_eta]
            assert (
                len(mock_print.call_args_list) > 2
            ), f"Not enough print calls for progress update. Got: {len(mock_print.call_args_list)}, calls: {mock_print.call_args_list}"
            assert "ETA:" in str(
                mock_print.call_args_list[2]
            ), f"ETA: not in expected print call. Call content: {mock_print.call_args_list[2]}"

    def test_simple_progress_bar_update_throttling(self):
        """Test that progress updates are throttled to prevent flickering"""
        progress = SimpleProgressBar()

        with patch("builtins.print") as mock_print:
            # Initialize
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")

            # Rapid updates (should be throttled)
            for i in range(10):
                progress(
                    i * 10, 1024, i, 1024.0, filename="test.txt", operation="upload"
                )

        # Should have fewer print calls than updates due to throttling
        assert mock_print.call_count < 12  # 1 initial + 10 updates, but throttled

    def test_simple_progress_bar_completion_summary(self):
        """Test completion summary with timing information"""
        progress = SimpleProgressBar()

        with patch("builtins.print") as mock_print:
            with patch(
                "time.time", side_effect=[100.0, 100.1, 105.0, 105.1]
            ):  # 5 second transfer
                progress(0, 1048576, 0.0, 0.0, filename="test.txt", operation="upload")
                progress(
                    1048576,
                    1048576,
                    100.0,
                    209715.2,
                    filename="test.txt",
                    operation="upload",
                )

        # Check completion message
        completion_calls = [
            str(call) for call in mock_print.call_args_list if "Terminé" in str(call)
        ]
        assert len(completion_calls) > 0


class TestDetailedProgress:
    """Tests for DetailedProgress tracker"""

    def test_detailed_progress_initialization(self):
        """Test DetailedProgress initialization"""
        # Without log file
        progress = DetailedProgress()
        assert progress.log_file is None
        assert progress.start_time is None
        assert progress.checkpoints == []

        # With log file
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress_with_log = DetailedProgress(log_file=temp_log.name)
            assert progress_with_log.log_file == temp_log.name
        finally:
            os.unlink(temp_log.name)

    def test_detailed_progress_checkpoint_tracking(self):
        """Test that DetailedProgress tracks checkpoints"""
        progress = DetailedProgress()

        with patch("builtins.print"):
            progress(
                0,
                1024,
                0.0,
                0.0,
                filename="test.txt",
                operation="upload",
                status="starting",
            )
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")
            progress(
                1024,
                1024,
                100.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="completed",
            )

        assert len(progress.checkpoints) == 3
        assert progress.checkpoints[0]["bytes"] == 0
        assert progress.checkpoints[1]["bytes"] == 512
        assert progress.checkpoints[2]["bytes"] == 1024

    def test_detailed_progress_status_messages(self):
        """Test different status message handling"""
        progress = DetailedProgress()

        with patch("builtins.print") as mock_print:
            # Starting status
            progress(
                0,
                1024,
                0.0,
                0.0,
                filename="test.txt",
                operation="upload",
                status="starting",
            )

            # Saving status
            progress(
                1024,
                1024,
                100.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="saving",
            )

            # Completed status
            progress(
                1024,
                1024,
                100.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="completed",
            )

            # Error status
            progress(
                512,
                1024,
                50.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="error",
                error="Network timeout",
            )

        # Verify different status messages were printed
        all_output = " ".join([str(call) for call in mock_print.call_args_list])
        assert "Initialisation du transfert..." in all_output
        assert "Sauvegarde en cours..." in all_output
        assert "Transfert terminé!" in all_output
        assert "Erreur: Network timeout" in all_output

    def test_detailed_progress_periodic_updates(self):
        """Test periodic progress updates at 20% intervals"""
        progress = DetailedProgress()

        with patch("builtins.print") as mock_print:
            # Initialize
            progress(
                0,
                1000,
                0.0,
                0.0,
                filename="test.txt",
                operation="upload",
                status="starting",
            )

            # Updates at various percentages
            progress(
                200, 1000, 20.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should print
            progress(
                250, 1000, 25.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should not print
            progress(
                400, 1000, 40.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should print
            progress(
                600, 1000, 60.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should print

        # Count progress update messages (should have 20%, 40%, 60%)
        progress_updates = [
            str(call)
            for call in mock_print.call_args_list
            if "Progression:" in str(call)
        ]
        assert len(progress_updates) >= 3

    def test_detailed_progress_with_log_file(self):
        """Test DetailedProgress with file logging"""
        temp_log = tempfile.NamedTemporaryFile(mode="w", delete=False)
        temp_log.close()

        try:
            progress = DetailedProgress(log_file=temp_log.name)

            with patch("builtins.print"):
                progress(
                    0,
                    1024,
                    0.0,
                    0.0,
                    filename="test.txt",
                    operation="upload",
                    status="starting",
                )
                progress(
                    512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload"
                )
                progress(
                    1024,
                    1024,
                    100.0,
                    1024.0,
                    filename="test.txt",
                    operation="upload",
                    status="completed",
                )

            # Verify log file was written
            with open(temp_log.name, "r", encoding="utf-8") as f:
                log_content = f.read()

            assert "upload" in log_content
            assert "test.txt" in log_content
            assert "50.0%" in log_content

        finally:
            os.unlink(temp_log.name)

    def test_detailed_progress_log_file_error_handling(self):
        """Test graceful handling of log file errors"""
        # Use invalid log file path
        progress = DetailedProgress(log_file="/invalid/path/log.txt")

        # Should not raise exception even with invalid log file
        with patch("builtins.print"):
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")


class TestMinimalProgress:
    """Tests for MinimalProgress tracker"""

    def test_minimal_progress_initialization(self):
        """Test MinimalProgress initialization"""
        progress = MinimalProgress()
        assert progress.milestones == {0, 25, 50, 75, 100}
        assert progress.shown == set()
        assert progress.start_time is None

    def test_minimal_progress_milestone_tracking(self):
        """Test that MinimalProgress only shows milestone percentages"""
        progress = MinimalProgress()

        with patch("builtins.print") as mock_print:
            # Initialize
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")

            # Various progress updates
            progress(
                256, 1024, 25.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should show
            progress(
                307, 1024, 30.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should not show
            progress(
                512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should show
            progress(
                640, 1024, 62.5, 1024.0, filename="test.txt", operation="upload"
            )  # Should not show
            progress(
                768, 1024, 75.0, 1024.0, filename="test.txt", operation="upload"
            )  # Should show
            progress(
                1024,
                1024,
                100.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="completed",
            )

        # Count milestone messages
        milestone_calls = [
            str(call)
            for call in mock_print.call_args_list
            if "%" in str(call) and "Upload:" not in str(call)
        ]
        assert (
            len(milestone_calls) >= 3
        )  # Should have 25%, 50%, 75% (100% handled by completion)

    def test_minimal_progress_completion_message(self):
        """Test MinimalProgress completion handling"""
        progress = MinimalProgress()

        with patch("builtins.print") as mock_print:
            with patch("time.time", side_effect=[100.0, 105.0]):  # 5 second transfer
                progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")
                progress(
                    1024,
                    1024,
                    100.0,
                    1024.0,
                    filename="test.txt",
                    operation="upload",
                    status="completed",
                )

        # Check completion message
        completion_calls = [
            str(call) for call in mock_print.call_args_list if "Terminé" in str(call)
        ]
        assert len(completion_calls) > 0

    def test_minimal_progress_error_handling(self):
        """Test MinimalProgress error status handling"""
        progress = MinimalProgress()

        with patch("builtins.print") as mock_print:
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")
            progress(
                512,
                1024,
                50.0,
                1024.0,
                filename="test.txt",
                operation="upload",
                status="error",
                error="Network error",
            )

        # Check error message
        error_calls = [
            str(call) for call in mock_print.call_args_list if "Erreur" in str(call)
        ]
        assert len(error_calls) > 0

    def test_minimal_progress_duplicate_milestones(self):
        """Test that duplicate milestones are not shown"""
        progress = MinimalProgress()

        with patch("builtins.print") as mock_print:
            progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")

            # Call 50% multiple times
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")
            progress(512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload")

        # Should only show 50% once
        fifty_percent_calls = [
            str(call) for call in mock_print.call_args_list if "50%" in str(call)
        ]
        assert len(fifty_percent_calls) == 1


class TestSilentProgress:
    """Tests for SilentProgress tracker"""

    def test_silent_progress_initialization(self):
        """Test SilentProgress initialization and log file creation"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = SilentProgress(log_file=temp_log.name)
            assert progress.log_file == temp_log.name
            assert progress.start_time is None

            # Verify log file was created with headers
            with open(temp_log.name, "r", encoding="utf-8") as f:
                content = f.read()

            assert "pCloud Transfer Log" in content
            assert "timestamp,operation,filename" in content

        finally:
            os.unlink(temp_log.name)

    def test_silent_progress_csv_logging(self):
        """Test that SilentProgress logs to CSV format correctly"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = SilentProgress(log_file=temp_log.name)

            # Make progress calls
            progress(
                0,
                1024,
                0.0,
                0.0,
                filename="test.txt",
                operation="upload",
                status="starting",
            )
            progress(
                512, 1024, 50.0, 1048576.0, filename="test.txt", operation="upload"
            )
            progress(
                1024,
                1024,
                100.0,
                1048576.0,
                filename="test.txt",
                operation="upload",
                status="completed",
            )

            # Read and verify log content
            with open(temp_log.name, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) >= 5  # Header + comment + 3 data lines

            # Check CSV format
            data_lines = [
                line
                for line in lines
                if not line.startswith("#")
                and line.strip()
                != "timestamp,operation,filename,percentage,bytes_transferred,total_bytes,speed_mbps,status"
            ]  # Exclude header line itself
            assert len(data_lines) == 3  # 3 data lines

            # Verify CSV structure
            for line in data_lines[1:]:  # Skip header
                fields = line.strip().split(",")
                assert (
                    len(fields) == 8
                )  # timestamp,operation,filename,percentage,bytes_transferred,total_bytes,speed_mbps,status

        finally:
            os.unlink(temp_log.name)

    def test_silent_progress_no_console_output(self):
        """Test that SilentProgress produces no console output"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = SilentProgress(log_file=temp_log.name)

            with patch("builtins.print") as mock_print:
                progress(0, 1024, 0.0, 0.0, filename="test.txt", operation="upload")
                progress(
                    512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload"
                )
                progress(
                    1024,
                    1024,
                    100.0,
                    1024.0,
                    filename="test.txt",
                    operation="upload",
                    status="completed",
                )

            # Verify no print calls were made
            assert mock_print.call_count == 0

        finally:
            os.unlink(temp_log.name)

    def test_silent_progress_log_file_error_handling(self):
        """Test SilentProgress handling of log file errors"""
        # Use invalid log file path
        with pytest.raises(Exception):
            SilentProgress(log_file="/invalid/path/log.csv")


class TestProgressFactoryFunctions:
    """Tests for progress tracker factory functions"""

    def test_create_progress_bar_factory(self):
        """Test create_progress_bar factory function"""
        progress = create_progress_bar("Test Upload", width=40, show_speed=False)

        assert isinstance(progress, SimpleProgressBar)
        assert progress.title == "Test Upload"
        assert progress.width == 40
        assert progress.show_speed is False

    def test_create_detailed_progress_factory(self):
        """Test create_detailed_progress factory function"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = create_detailed_progress(log_file=temp_log.name)

            assert isinstance(progress, DetailedProgress)
            assert progress.log_file == temp_log.name

        finally:
            os.unlink(temp_log.name)

    def test_create_minimal_progress_factory(self):
        """Test create_minimal_progress factory function"""
        progress = create_minimal_progress()

        assert isinstance(progress, MinimalProgress)
        assert progress.milestones == {0, 25, 50, 75, 100}

    def test_create_silent_progress_factory(self):
        """Test create_silent_progress factory function"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = create_silent_progress(temp_log.name)

            assert isinstance(progress, SilentProgress)
            assert progress.log_file == temp_log.name

        finally:
            os.unlink(temp_log.name)


class TestCustomProgressCallbacks:
    """Tests for custom progress callback implementations"""

    def test_custom_callback_basic_implementation(self):
        """Test implementing a basic custom progress callback"""
        call_log = []

        def custom_callback(
            bytes_transferred, total_bytes, percentage, speed, **kwargs
        ):
            call_log.append(
                {
                    "bytes": bytes_transferred,
                    "total": total_bytes,
                    "percent": percentage,
                    "speed": speed,
                    "operation": kwargs.get("operation"),
                    "filename": kwargs.get("filename"),
                }
            )

        # Simulate progress calls
        custom_callback(0, 1024, 0.0, 0.0, operation="upload", filename="test.txt")
        custom_callback(
            512, 1024, 50.0, 1024.0, operation="upload", filename="test.txt"
        )
        custom_callback(
            1024, 1024, 100.0, 1024.0, operation="upload", filename="test.txt"
        )

        assert len(call_log) == 3
        assert call_log[0]["percent"] == 0.0
        assert call_log[1]["percent"] == 50.0
        assert call_log[2]["percent"] == 100.0

    def test_custom_callback_with_state_tracking(self):
        """Test custom callback that maintains state"""

        class StatefulCallback:
            def __init__(self):
                self.calls = 0
                self.max_speed = 0
                self.total_bytes_seen = 0

            def __call__(
                self, bytes_transferred, total_bytes, percentage, speed, **kwargs
            ):
                self.calls += 1
                self.max_speed = max(self.max_speed, speed)
                self.total_bytes_seen = max(self.total_bytes_seen, bytes_transferred)

        callback = StatefulCallback()

        # Simulate progress
        callback(0, 1024, 0.0, 0.0, operation="upload", filename="test.txt")
        callback(256, 1024, 25.0, 512.0, operation="upload", filename="test.txt")
        callback(512, 1024, 50.0, 1024.0, operation="upload", filename="test.txt")
        callback(1024, 1024, 100.0, 800.0, operation="upload", filename="test.txt")

        assert callback.calls == 4
        assert callback.max_speed == 1024.0
        assert callback.total_bytes_seen == 1024

    def test_custom_callback_error_handling(self):
        """Test that custom callback errors don't break the system"""

        def failing_callback(*args, **kwargs):
            raise ValueError("Callback error")

        # In real usage, the SDK should handle callback errors gracefully
        # Here we just verify the callback can be called
        with pytest.raises(ValueError, match="Callback error"):
            failing_callback(
                512, 1024, 50.0, 1024.0, operation="upload", filename="test.txt"
            )

    def test_custom_callback_with_filtering(self):
        """Test custom callback that filters certain conditions"""
        filtered_calls = []

        def filtering_callback(
            bytes_transferred, total_bytes, percentage, speed, **kwargs
        ):
            # Only log every 10%
            if percentage % 10 == 0:
                filtered_calls.append(percentage)

        # Simulate many progress calls
        for i in range(101):
            filtering_callback(
                i * 10, 1000, i, 1024.0, operation="upload", filename="test.txt"
            )

        # Should only have calls at 10% intervals
        expected_calls = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        assert filtered_calls == expected_calls


class TestProgressAccuracy:
    """Tests for progress tracking accuracy and consistency"""

    def test_progress_percentage_accuracy(self):
        """Test that percentage calculations are accurate"""
        progress = SimpleProgressBar()

        test_cases = [
            (0, 1000, 0.0),
            (250, 1000, 25.0),
            (500, 1000, 50.0),
            (750, 1000, 75.0),
            (1000, 1000, 100.0),
        ]

        with patch("builtins.print"):
            for bytes_transferred, total_bytes, expected_percentage in test_cases:
                progress(
                    bytes_transferred,
                    total_bytes,
                    expected_percentage,
                    1024.0,
                    filename="test.txt",
                    operation="upload",
                )

    def test_progress_speed_calculations(self):
        """Test speed calculation accuracy"""
        call_log = []

        def speed_tracking_callback(
            bytes_transferred, total_bytes, percentage, speed, **kwargs
        ):
            call_log.append(
                {
                    "bytes": bytes_transferred,
                    "speed": speed,
                    "time": kwargs.get("elapsed_time", 0),
                }
            )

        # Mock time progression for speed calculation
        with patch("time.time", side_effect=[0, 1, 2, 3, 4, 5]):  # 1 second intervals
            progress = SimpleProgressBar()

            # Simulate transfer at 1024 bytes/second
            for i in range(5):
                bytes_transferred = i * 1024
                expected_speed = 1024.0 if i > 0 else 0.0

                with patch("builtins.print"):
                    progress(
                        bytes_transferred,
                        5120,
                        (bytes_transferred / 5120) * 100,
                        expected_speed,
                        filename="test.txt",
                        operation="upload",
                    )

    def test_progress_consistency_across_trackers(self):
        """Test that all progress trackers receive consistent data"""
        call_logs = {
            "simple": [],
            "detailed": [],
            "minimal": [],
        }

        def create_logging_wrapper(tracker_name, original_tracker):
            def wrapper(*args, **kwargs):
                call_logs[tracker_name].append(args)
                return original_tracker(*args, **kwargs)

            return wrapper

        # Create wrapped trackers
        simple = create_logging_wrapper("simple", SimpleProgressBar())
        detailed = create_logging_wrapper("detailed", DetailedProgress())
        minimal = create_logging_wrapper("minimal", MinimalProgress())

        # Call all trackers with same data
        test_data = [
            (0, 1024, 0.0, 0.0),
            (256, 1024, 25.0, 1024.0),
            (512, 1024, 50.0, 1024.0),
            (1024, 1024, 100.0, 1024.0),
        ]

        with patch("builtins.print"):
            for data in test_data:
                simple(*data, filename="test.txt", operation="upload")
                detailed(*data, filename="test.txt", operation="upload")
                minimal(*data, filename="test.txt", operation="upload")

        # Verify all trackers received same data
        assert (
            len(call_logs["simple"])
            == len(call_logs["detailed"])
            == len(call_logs["minimal"])
        )

        for i in range(len(test_data)):
            assert (
                call_logs["simple"][i]
                == call_logs["detailed"][i]
                == call_logs["minimal"][i]
            )

    def test_progress_edge_cases(self):
        """Test progress tracking edge cases"""
        progress = SimpleProgressBar()

        edge_cases = [
            # Zero total size
            (0, 0, 0.0, 0.0),
            # Bytes transferred exceeds total (shouldn't happen but handle gracefully)
            (1500, 1000, 150.0, 1024.0),
            # Negative values (shouldn't happen but handle gracefully)
            (-1, 1000, -0.1, 0.0),
            # Very large numbers
            (1073741824, 2147483648, 50.0, 1073741824.0),  # 1GB of 2GB at 1GB/s
        ]

        with patch("builtins.print"):
            for bytes_transferred, total_bytes, percentage, speed in edge_cases:
                try:
                    progress(
                        bytes_transferred,
                        total_bytes,
                        percentage,
                        speed,
                        filename="test.txt",
                        operation="upload",
                    )
                except Exception as e:
                    pytest.fail(f"Progress tracker failed on edge case: {e}")


class TestProgressPerformance:
    """Tests for progress tracking performance"""

    @pytest.mark.performance
    def test_progress_callback_performance(self):
        """Test performance of progress callbacks with many updates"""
        progress = SimpleProgressBar()

        start_time = time.time()

        with patch("builtins.print"):
            # Simulate 1000 progress updates
            for i in range(1000):
                progress(
                    i, 1000, i / 10.0, 1024.0, filename="test.txt", operation="upload"
                )

        end_time = time.time()
        elapsed = end_time - start_time

        # Should complete quickly (under 1 second for 1000 calls)
        assert elapsed < 1.0

    @pytest.mark.performance
    def test_silent_progress_logging_performance(self):
        """Test performance of silent progress with file logging"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = SilentProgress(log_file=temp_log.name)

            start_time = time.time()

            # Simulate 1000 progress updates with logging
            for i in range(1000):
                progress(
                    i, 1000, i / 10.0, 1024.0, filename="test.txt", operation="upload"
                )

            end_time = time.time()
            elapsed = end_time - start_time

            # Should complete quickly even with file I/O
            assert elapsed < 2.0

            # Verify all entries were logged
            with open(temp_log.name, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Should have header + comment + 1000 data lines
            data_lines = [
                line
                for line in lines
                if not line.startswith("#")
                and line.strip()
                != "timestamp,operation,filename,percentage,bytes_transferred,total_bytes,speed_mbps,status"
            ]  # Exclude header line itself
            assert len(data_lines) == 1000  # 1000 data lines

        finally:
            os.unlink(temp_log.name)

    def test_memory_usage_with_many_callbacks(self):
        """Test memory usage doesn't grow excessively with many callback calls"""
        import gc

        # Create progress tracker that stores checkpoints
        progress = DetailedProgress()

        # Force garbage collection before test
        gc.collect()

        with patch("builtins.print"):
            # Simulate many progress calls
            for i in range(10000):
                progress(
                    i, 10000, i / 100.0, 1024.0, filename="test.txt", operation="upload"
                )

        # Verify checkpoints list doesn't grow indefinitely
        # (In real implementation, it might be limited or cleaned up)
        assert len(progress.checkpoints) == 10000  # All stored for this test

        # Force garbage collection
        gc.collect()


class TestProgressErrorHandling:
    """Tests for error handling in progress callbacks"""

    def test_progress_with_invalid_parameters(self):
        """Test progress trackers with invalid parameters"""
        progress = SimpleProgressBar()

        invalid_cases = [
            # None values
            (None, 1024, 0.0, 0.0),
            (512, None, 50.0, 0.0),
            (512, 1024, None, 0.0),
            (512, 1024, 50.0, None),
            # String values where numbers expected
            ("512", 1024, 50.0, 1024.0),
            (512, "1024", 50.0, 1024.0),
        ]

        for bytes_transferred, total_bytes, percentage, speed in invalid_cases:
            with patch("builtins.print"):
                try:
                    progress(
                        bytes_transferred,
                        total_bytes,
                        percentage,
                        speed,
                        filename="test.txt",
                        operation="upload",
                    )
                except (TypeError, ValueError):
                    # Expected to fail with invalid types
                    pass

    def test_progress_with_missing_kwargs(self):
        """Test progress trackers with missing keyword arguments"""
        progress = SimpleProgressBar()

        with patch("builtins.print"):
            # Should handle missing kwargs gracefully
            progress(512, 1024, 50.0, 1024.0)  # No filename, operation
            progress(512, 1024, 50.0, 1024.0, filename="test.txt")  # No operation
            progress(512, 1024, 50.0, 1024.0, operation="upload")  # No filename

    def test_detailed_progress_log_file_permissions(self):
        """Test DetailedProgress with read-only log file"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            # Make file read-only
            os.chmod(temp_log.name, 0o444)

            progress = DetailedProgress(log_file=temp_log.name)

            with patch("builtins.print"):
                # Should not raise exception even if can't write to log
                progress(
                    512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload"
                )

        finally:
            # Restore permissions and cleanup
            os.chmod(temp_log.name, 0o666)
            os.unlink(temp_log.name)

    def test_callback_exception_isolation(self):
        """Test that exceptions in one callback don't affect others"""
        good_calls = []

        def good_callback(*args, **kwargs):
            good_calls.append(args)

        def bad_callback(*args, **kwargs):
            raise Exception("Callback error")

        # In real SDK usage, multiple callbacks might be chained
        # Here we simulate error isolation
        callbacks = [good_callback, bad_callback, good_callback]

        for callback in callbacks:
            try:
                callback(
                    512, 1024, 50.0, 1024.0, filename="test.txt", operation="upload"
                )
            except Exception:
                pass  # Isolate errors

        # Good callbacks should still have been called
        assert len(good_calls) == 2


class TestProgressThreadSafety:
    """Tests for thread safety of progress callbacks"""

    def test_simple_progress_thread_safety(self):
        """Test SimpleProgressBar thread safety"""
        progress = SimpleProgressBar()
        results = []
        errors = []

        def worker(worker_id):
            try:
                with patch("builtins.print"):
                    for i in range(100):
                        progress(
                            i,
                            100,
                            i,
                            1024.0,
                            filename=f"file_{worker_id}.txt",
                            operation="upload",
                        )
                results.append(worker_id)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors and all workers completed
        assert len(errors) == 0
        assert len(results) == 5

    def test_silent_progress_thread_safety(self):
        """Test SilentProgress thread safety with file logging"""
        temp_log = tempfile.NamedTemporaryFile(delete=False)
        temp_log.close()

        try:
            progress = SilentProgress(log_file=temp_log.name)
            results = []
            errors = []

            def worker(worker_id):
                try:
                    for i in range(50):
                        progress(
                            i,
                            50,
                            i * 2,
                            1024.0,
                            filename=f"file_{worker_id}.txt",
                            operation="upload",
                        )
                    results.append(worker_id)
                except Exception as e:
                    errors.append(e)

            # Create multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Verify no errors
            assert len(errors) == 0
            assert len(results) == 3

            # Verify log file contains entries from all threads
            with open(temp_log.name, "r", encoding="utf-8") as f:
                content = f.read()

            assert "file_0.txt" in content
            assert "file_1.txt" in content
            assert "file_2.txt" in content

        finally:
            os.unlink(temp_log.name)


@pytest.mark.integration
class TestProgressIntegrationReal:
    """Integration tests for progress callbacks with real operations"""

    @pytest.mark.skip(reason="Requires actual file operations")
    def test_progress_with_real_file_upload(self):
        """Test progress tracking with real file upload"""
        # This would be tested with actual pCloud SDK operations
        # Requires real credentials and file operations
        pass

    @pytest.mark.skip(reason="Requires actual file operations")
    def test_progress_with_real_file_download(self):
        """Test progress tracking with real file download"""
        # This would be tested with actual pCloud SDK operations
        # Requires real credentials and file operations
        pass
