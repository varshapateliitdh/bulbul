import ssl
import httpx
from fastapi import APIRouter, HTTPException
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
    httpx_client=httpx.Client(verify=_no_verify_ctx),
)


logger = logging.getLogger(__name__)
router = APIRouter(
    responses={404: {"description": "Not found"}},
)


@router.post("/read_aloud", status_code=200)
async def speech_to_text(answer: str, language_code: str = "en-IN"):
    try:
        audio = client.text_to_speech.convert(
            target_language_code=language_code,
            text=answer,
            model="bulbul:v3",
            speaker="shubh"
        )
        save(audio, "output1.wav")
        return "output1.wav"

    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {e}")
        raise HTTPException(status_code=500, detail="Text-to-speech conversion failed")
