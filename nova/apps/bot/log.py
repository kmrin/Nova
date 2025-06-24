import os
import shutil
import logging
import traceback

from datetime import datetime
from typing import Optional

from logging import (
    Logger as LoggingLogger,
    Formatter, FileHandler, StreamHandler,
    INFO, ERROR, CRITICAL, DEBUG,
    getLogger
)

from .conf import conf
from .paths import Path

BOLD = "\x1b[1m"
RESET = "\x1b[0m"


class LoggingFormatter(Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLOURS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold
    }

    def format(self, record):
        log_color = self.COLOURS.get(record.levelno)

        format_str = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format_str = format_str.replace("(black)", self.black + self.bold)
        format_str = format_str.replace("(reset)", self.reset)
        format_str = format_str.replace("(levelcolor)", log_color if log_color is not None else "")
        format_str = format_str.replace("(green)", self.green + self.bold)

        formatter = logging.Formatter(format_str, "%d-%m-%y %H:%M:%S", style="{")

        return formatter.format(record)

log_filename_latest = os.path.join(Path.LOG_LATEST)
log_dirname_latest = os.path.dirname(log_filename_latest)

if os.path.exists(log_filename_latest):
    try:
        creation_time = os.path.getctime(log_filename_latest)
        old_timestamp = datetime.fromtimestamp(creation_time).strftime("%d.%m.%y-%H%M%S")

        os.makedirs(log_dirname_latest, exist_ok=True)
        shutil.move(log_filename_latest, os.path.join(Path.LOG_HISTORY, f"nova-{old_timestamp}.log"))

    except FileNotFoundError:
        os.remove(log_filename_latest)

console_handler = StreamHandler()
console_handler.setFormatter(LoggingFormatter())

file_handler = FileHandler(
    filename=log_filename_latest,
    mode="a",
    encoding="utf-8",
    delay=False
)

file_handler.setFormatter(
    Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", "%d-%m-%y %H:%M:%S",
        style="{"
    )
)

root_logger = getLogger("RinBot")
root_logger.setLevel(DEBUG if conf.debug else INFO)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)


class Logger:
    ROOT: LoggingLogger           = root_logger
    COMMAND_CHECKS: LoggingLogger = getLogger("Command Checks")
    CLIENT: LoggingLogger         = getLogger("Client")
    COMMANDS: LoggingLogger       = getLogger("Commands")
    DB: LoggingLogger             = getLogger("Database")
    EVENTS: LoggingLogger         = getLogger("Events")
    EXTENSIONS: LoggingLogger     = getLogger("Extensions")
    ERRORS: LoggingLogger         = getLogger("Errors")
    GENERIC_CHECKS: LoggingLogger = getLogger("Generic Checks")
    GEMINI: LoggingLogger         = getLogger("Gemini")
    HELPERS: LoggingLogger        = getLogger("Helpers")
    INTERFACE: LoggingLogger      = getLogger("Interface")
    LOCALE: LoggingLogger         = getLogger("Localisation")
    MUSIC: LoggingLogger          = getLogger("Music")
    PROGRAMS: LoggingLogger       = getLogger("Programs")
    STARTUP_CHECKS: LoggingLogger = getLogger("Startup Checks")
    TASKS: LoggingLogger          = getLogger("Tasks")
    TREE: LoggingLogger           = getLogger("Tree")
    LOADER: LoggingLogger         = getLogger("Loader")
    JSON: LoggingLogger           = getLogger("JSON")
    YAML: LoggingLogger           = getLogger("YAML")
    RESPONDER: LoggingLogger      = getLogger("Responder")
    SUBCLASSES: LoggingLogger     = getLogger("SubClasses")
    WEB: LoggingLogger            = getLogger("Web")
    UTILS: LoggingLogger          = getLogger("Utils")

    if conf.forward_discord_logs:
        DISCORD: LoggingLogger = getLogger("discord")


for logger_name, custom_logger in vars(Logger).items():
    if isinstance(custom_logger, LoggingLogger) and logger_name != "root":
        custom_logger.setLevel(DEBUG if conf.debug else INFO)
        custom_logger.propagate = True
        custom_logger.addHandler(console_handler)
        custom_logger.addHandler(file_handler)


def format_exception(e: Exception) -> str:
    path, line, _, _ = traceback.extract_tb(e.__traceback__)[-1]
    return f"{type(e).__name__} [{os.path.basename(path)} | {line}] -> {str(e)}"


def log_exception(
        e: Exception,
        logger: Optional[LoggingLogger] = None,
        critical: bool = False,
        log_trace: bool = True
) -> str:
    formatted = format_exception(e)

    level = CRITICAL if critical else ERROR

    if not logger:
        logger = Logger.ROOT

    logger.log(level, formatted)

    if log_trace:
        trace = traceback.format_exception(type(e), e, e.__traceback__)
        trace = "".join(trace)

        now = datetime.now().strftime("%d.%m.%y-%H%M%S")

        filename = f"{type(e).__name__}-{now}.txt"
        filepath = os.path.join(Path.LOG_TRACEBACKS, filename)
        filedir = os.path.dirname(filepath)

        os.makedirs(filedir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(trace)

    return formatted