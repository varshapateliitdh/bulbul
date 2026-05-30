import ssl
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import logging
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save
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
    httpx_client=httpx.Client(verify=_no_verify_ctx, timeout=60.0),
)


logger = logging.getLogger(__name__)
router = APIRouter(
    responses={404: {"description": "Not found"}},
)


def detect_language(text: str) -> str:
    """
    Detect the language of the *text* using Sarvam's language identification API,
    falling back to 'en-IN' on any failure or timeout.
    """
    from sarvamai.core import RequestOptions  # noqa: PLC0415 (local import intentional)
    try:
        response = client.text.identify_language(
            input=text,
            request_options=RequestOptions(timeout_in_seconds=30),
        )
        code = getattr(response, "language_code", None)
        if code:
            logger.info(f"Language identification response: {code}")
            return code
    except Exception as e:
        logger.error(f"Failed to detect language: {e}")

    return 'en-IN'


@router.post("/read_aloud", status_code=200)
async def text_to_speech(answer: str):
    from sarvamai.core import RequestOptions
    try:
        # Detect the actual language of the assistant's response
        detected_language = detect_language(answer)
        logger.info(
            f"TTS requested. Detected response language: {detected_language}")

        audio = client.text_to_speech.convert(
            target_language_code=detected_language,
            text=answer,
            model="bulbul:v3",
            speaker="shubh",
            request_options=RequestOptions(timeout_in_seconds=30),
        )
        output_path = os.path.join(
            os.path.dirname(__file__), "..", "output1.wav")
        save(audio, output_path)
        return FileResponse(output_path, media_type="audio/wav", filename="output.wav")

    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {e}")
        raise HTTPException(
            status_code=500, detail="Text-to-speech conversion failed")
