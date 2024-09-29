from enum import Enum

from pydantic import Field

from wiederverwendbar.starlette_admin.settings.settings import AdminSettings


class ActionLogAdminSettings(AdminSettings):
    class LogLevels(str, Enum):
        """
        Log levels
        """

        CRITICAL = "CRITICAL"
        FATAL = "FATAL"
        ERROR = "ERROR"
        WARNING = "WARNING"
        INFO = "INFO"
        DEBUG = "DEBUG"

    action_log_level: LogLevels = Field(default=LogLevels.INFO,
                                        title="Action Log Level",
                                        description="The action log level")
    action_log_ignore_loggers_equal: list[str] = Field(default_factory=list,
                                                       title="Action Log Ignore Loggers Equal",
                                                       description="List of loggers to ignore equal")
    action_log_ignore_loggers_like: list[str] = Field(default_factory=list,
                                                      title="Action Log Ignore Loggers Like",
                                                      description="List of loggers to ignore like")
    action_log_formatter: str = Field(default="%(asctime)s - %(levelname)s - %(message)s",
                                      title="Action Log Formatter",
                                      description="The action log formatter")
    action_log_wait_for_websocket: bool = Field(default=True,
                                                title="Action Log Wait For WebSocket",
                                                description="Wait for the websocket to be ready")
    action_log_wait_for_websocket_timeout: int = Field(default=5,
                                                       title="Action Log Wait For WebSocket Timeout",
                                                       description="The action log wait for websocket timeout")
    action_log_show_errors: bool = Field(default=True,
                                         title="Action Log Show Errors",
                                         description="Show errors in the action log")
    action_log_halt_on_error: bool = Field(default=True,
                                           title="Action Log Halt On Error",
                                           description="Halt on error in the action log")
    action_log_use_context_logger_level: bool = Field(default=True,
                                                      title="Action Log Use Context Logger Level",
                                                      description="Use the context logger level in the action log")
    action_log_use_context_logger_level_on_not_set: bool = Field(default=True,
                                                                 title="Action Log Use Context Logger Level On Not Set",
                                                                 description="Use the context logger level on not set in the action log")
    action_log_handle_origin_logger: bool = Field(default=True,
                                                  title="Action Log Handle Origin Logger",
                                                  description="Handle the origin logger in the action log")
