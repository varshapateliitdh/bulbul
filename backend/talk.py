import asyncio
import ssl
import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import logging
import tempfile
from dotenv import load_dotenv
from sarvamai import SarvamAI
from backend.chat import generate_chat_stream, generate_doc_data
from fastapi.responses import StreamingResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

_no_verify_ctx = ssl.create_default_context()
_no_verify_ctx.check_hostname = False
_no_verify_ctx.verify_mode = ssl.CERT_NONE

client = SarvamAI(
    api_subscription_key=os.environ.get("SARVAM_API_KEY"),
    httpx_client=httpx.Client(verify=_no_verify_ctx),
)


logger = logging.getLogger(__name__)
router = APIRouter(
    responses={404: {"description": "Not found"}},
)


@router.post("/talk", status_code=200)
async def speech_to_text(file: UploadFile = File(...)):

    if file.content_type not in (
        "audio/mpeg",
        "audio/mp3"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only MP3 files are supported"
        )

    with tempfile.TemporaryDirectory() as tmpdir:

        input_path = os.path.join(
            tmpdir,
            "input.mp3"
        )

        try:
            contents = await file.read()

            with open(input_path, "wb") as f:
                f.write(contents)

            logger.info(
                "File saved successfully"
            )

        except Exception as e:
            logger.error(
                f"Error saving file: {e}"
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to save file"
            )

        def process_document():

            with open(
                input_path,
                "rb"
            ) as audio_file:

                response = (
                    client.speech_to_text
                    .transcribe(
                        file=audio_file,
                        model="saaras:v3",
                        mode="transcribe",
                        language_code="unknown",
                    )
                )

            logger.info(
                "Speech-to-text successful"
            )

            logger.info(
                f"response: {response}"
            )

            return response.transcript

        try:
            transcript = (
                await asyncio.to_thread(
                    process_document
                )
            )

            doc_data = (
                generate_doc_data()
            )

            return StreamingResponse(
                generate_chat_stream(
                    transcript,
                    doc_data
                ),
                media_type="text/plain"
            )

        except Exception as e:

            logger.error(
                f"Document processing failed: {e}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Document processing "
                    "failed"
                )
            )
