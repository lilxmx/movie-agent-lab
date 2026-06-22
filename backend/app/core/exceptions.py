"""统一业务异常与全局异常处理。"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.response import ApiResponse


class BusinessError(Exception):
    def __init__(self, message: str, code: int = 1):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthError(BusinessError):
    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(message, code=1002)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def _handle_business(_: Request, exc: BusinessError) -> JSONResponse:
        status = 401 if isinstance(exc, AuthError) else 200
        return JSONResponse(
            status_code=status,
            content=ApiResponse.fail(exc.message, exc.code).model_dump(),
        )
