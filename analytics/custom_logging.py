import json
import logging
import sys
import time

import structlog
from asgi_correlation_id.context import correlation_id
from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute
from structlog.types import EventDict, Processor
from uvicorn.protocols.utils import get_path_with_query_string

logger = structlog.stdlib.get_logger("ark")


# https://github.com/hynek/structlog/issues/35#issuecomment-591321744
def rename_event_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(json_logs: bool = False, log_level: str = "INFO"):
    # Disable logs by third party libraries
    # Change to INFO if more details needed
    logging.getLogger().setLevel(log_level)
    logging.getLogger("fastapi_azure_auth").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        # We rename the `event` key to `message` only in JSON logs, as Datadog looks for the
        # `message` key but the pretty ConsoleRenderer looks for `event`
        shared_processors.append(rename_event_key)
        # Format the exception only for JSON logs, as we want to pretty-print them when
        # using the ConsoleRenderer
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=shared_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor
    if json_logs:
        log_renderer = structlog.processors.JSONRenderer()
    else:
        log_renderer = structlog.dev.ConsoleRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    for _log in ["uvicorn", "uvicorn.error"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True
        logging.getLogger(_log).setLevel(log_level)

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    logging.getLogger("api.access").setLevel(log_level)
    logging.getLogger("semd").setLevel(log_level)

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


class LoggingRoute(APIRoute):
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request):
            structlog.contextvars.clear_contextvars()
            # These context vars will be added to all log entries emitted during the request
            request_id = correlation_id.get()
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
                path=request.url.path,
                route=request.scope["route"].path,
            )

            start_time = time.perf_counter_ns()
            try:
                response = await original_route_handler(request)
            except HTTPException as http_exc:
                # Handle HTTPException separately to preserve its status code
                exc_content = json.dumps({"detail": http_exc.detail})
                response = Response(
                    status_code=http_exc.status_code,
                    content=exc_content,
                    media_type="application/json",
                )
                logger.warning(
                    f"HTTPException in route handler, {exc_content}",
                    status_code=http_exc.status_code,
                )
            except Exception as exc:
                # Fallback to generic error
                exc_content = json.dumps({"detail": "Internal Server Error"})
                response = Response(
                    status_code=500, content=exc_content, media_type="application/json"
                )
                logger.exception(f"Uncaught exception in route handler, {exc}")
            finally:
                process_time = time.perf_counter_ns() - start_time
                self.log_request(request, response, process_time, request_id)
                response.headers["X-Process-Time"] = str(process_time / 10**9)
                return response

        return custom_route_handler

    def log_request(
        self, request: Request, response: Response, process_time: int, request_id: str
    ):
        access_logger = structlog.stdlib.get_logger("api.access")
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)
        client_host = request.client.host
        client_port = request.client.port
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information
        log_message = f"""{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}"""
        process_time = process_time / 10**9

        # Replace isEnabledFor check with structlog's level approach
        log_level = logging.getLogger("api.access").getEffectiveLevel()

        if log_level <= logging.DEBUG:
            # if access_logger.isEnabledFor(logging.DEBUG):
            access_logger.debug(
                log_message,
                http={
                    "url": str(request.url),
                    "status_code": status_code,
                    "method": http_method,
                    "request_id": request_id,
                    "version": http_version,
                },
                network={"client": {"ip": client_host, "port": client_port}},
                duration=process_time,
            )
        elif log_level <= logging.INFO:
            # elif access_logger.isEnabledFor(logging.INFO):
            access_logger.info(
                log_message,
                duration=process_time,
            )
