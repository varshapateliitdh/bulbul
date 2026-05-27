from dotenv import load_dotenv
import uvicorn
from backend.upload_file import router as upload_file_router
from backend.chat import router as chat_router
from backend.talk import router as talk_router
from backend.read_aloud import router as read_aloud_router
from fastapi import FastAPI
import ssl
import httpx

# Disable SSL verification to work around corporate Zscaler proxy
_no_verify_ctx = ssl.create_default_context()
_no_verify_ctx.check_hostname = False
_no_verify_ctx.verify_mode = ssl.CERT_NONE

_orig_client_init = httpx.Client.__init__


def _patched_client_init(self, *args, **kwargs):
    kwargs.setdefault("verify", _no_verify_ctx)
    _orig_client_init(self, *args, **kwargs)


httpx.Client.__init__ = _patched_client_init

_orig_async_client_init = httpx.AsyncClient.__init__


def _patched_async_client_init(self, *args, **kwargs):
    kwargs.setdefault("verify", _no_verify_ctx)
    _orig_async_client_init(self, *args, **kwargs)


httpx.AsyncClient.__init__ = _patched_async_client_init


load_dotenv(dotenv_path="../.env")

app = FastAPI()

app.include_router(upload_file_router)
app.include_router(chat_router)
app.include_router(talk_router)
app.include_router(read_aloud_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
