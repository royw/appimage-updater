from types import SimpleNamespace
from unittest.mock import Mock, patch

from appimage_updater.instrumentation.factory import create_http_tracker_from_params


class TestCreateHttpTrackerFromParams:
    def test_returns_none_when_no_instrumentation(self) -> None:
        params = SimpleNamespace(instrument_http=False, trace=False)

        result = create_http_tracker_from_params(params)  # type: ignore[arg-type]

        assert result is None

    @patch("appimage_updater.instrumentation.factory.HTTPTracker")
    @patch("appimage_updater.instrumentation.factory.create_trace_http_logger")
    def test_trace_enabled_uses_trace_logger(self, mock_trace_logger: Mock, mock_tracker: Mock) -> None:
        params = SimpleNamespace(
            instrument_http=True,
            trace=True,
            http_stack_depth=5,
            http_track_headers=True,
        )

        logger_instance = Mock()
        mock_trace_logger.return_value = logger_instance

        create_http_tracker_from_params(params)  # type: ignore[arg-type]

        mock_trace_logger.assert_called_once_with(use_rich=True)
        mock_tracker.assert_called_once()
        _, kwargs = mock_tracker.call_args
        assert kwargs["stack_depth"] == 5
        assert kwargs["track_headers"] is True
        assert kwargs["logger"] is logger_instance

    @patch("appimage_updater.instrumentation.factory.HTTPTracker")
    @patch("appimage_updater.instrumentation.factory.create_default_http_logger")
    def test_instrument_http_uses_default_logger(self, mock_default_logger: Mock, mock_tracker: Mock) -> None:
        params = SimpleNamespace(
            instrument_http=True,
            trace=False,
            http_stack_depth=3,
            http_track_headers=False,
            debug=True,
        )

        logger_instance = Mock()
        mock_default_logger.return_value = logger_instance

        create_http_tracker_from_params(params)  # type: ignore[arg-type]

        mock_default_logger.assert_called_once_with(verbose=True)
        mock_tracker.assert_called_once()
        _, kwargs = mock_tracker.call_args
        assert kwargs["stack_depth"] == 3
        assert kwargs["track_headers"] is False
        assert kwargs["logger"] is logger_instance
