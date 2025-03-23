import logging
import sys
import json
import newrelic.agent
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar

request_id_context = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


class Logger:
    def __init__(self, log_file: str = "app.log"):
        log_format = "%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s"

        self.logger = logging.getLogger("AppLogger")
        self.logger.setLevel(logging.DEBUG)
        
        request_id_filter = RequestIdFilter()
        self.logger.addFilter(request_id_filter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))

        file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def send_log(self, message):
        """Logs an informational message"""
        if isinstance(message, dict):
            message = json.dumps(message)
        self.logger.info(message)
        self._send_to_newrelic('info', message)

    def send_debug(self, message):
        """Logs a debug message (for troubleshooting)"""
        if isinstance(message, dict):
            message = json.dumps(message)
        self.logger.debug(message)
        self._send_to_newrelic('debug', message)

    def send_warning(self, message):
        """Logs a warning message"""
        if isinstance(message, dict):
            message = json.dumps(message)
        self.logger.warning(message)
        self._send_to_newrelic('warning', message)

    def send_error(self, message):
        """Logs an error message"""
        if isinstance(message, dict):
            message = json.dumps(message)
        self.logger.error(message)
        self._send_to_newrelic('error', message)

    def send_critical(self, message):
        """Logs a critical error message (high severity)"""
        if isinstance(message, dict):
            message = json.dumps(message)
        self.logger.critical(message)
        self._send_to_newrelic('critical', message)

    @newrelic.agent.background_task(name='send_log_to_newrelic')
    def _send_to_newrelic(self, level, message):
        """Send logs to New Relic as log events"""
        try:
            request_id = request_id_context.get()

            nr_level = {
                'debug': 'DEBUG',
                'info': 'INFO',
                'warning': 'WARNING',
                'error': 'ERROR',
                'critical': 'CRITICAL'
            }.get(level, 'INFO')

            newrelic.agent.record_log_event(
                message=f"{request_id} - {message}",
                level=nr_level,
                attributes={
                    'requestId': request_id,
                    'request_id': request_id
                }
            )

            current_txn = newrelic.agent.current_transaction()
            if current_txn:
                current_txn.add_custom_attribute('requestId', request_id)
                current_txn.add_custom_attribute('request_id', request_id)

        except Exception as exception:
            self.logger.error(f"Failed to send log to New Relic: {str(exception)}")

logger = Logger()
