from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder

from analytics.custom_logging import logger


class APIError(HTTPException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _prefix: str = "API error"

    def __init__(self, what: str, **details):
        super().__init__(
            self._status_code,
            # status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"{self._prefix}: {what}",
                **jsonable_encoder(details),
            },
        )
        logger.warning(self.detail)


class NotFound(APIError):
    _status_code = status.HTTP_404_NOT_FOUND
    _prefix = "Not found"


class NotSupported(APIError):
    _status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    _prefix = "Not supported"


class AlreadyExists(APIError):
    _status_code = status.HTTP_409_CONFLICT
    _prefix = "Datapoint already exists"


class InvalidData(APIError):
    _status_code = status.HTTP_400_BAD_REQUEST
    _prefix = "Invalid data"


class NotAllowed(APIError):
    _status_code = status.HTTP_403_FORBIDDEN
    _prefix = "Forbidden"


class InternalError(APIError):
    _status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    _prefix = "Internal Server Error"
