import ssl
import httpx
import zipfile
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
import os
import logging
from dotenv import load_dotenv
from sarvamai import SarvamAI
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


def generate_chat_stream(user_message: str, doc_data: str):

    response = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {
                "role": "system",
                "content": """
You are a document assistant.

Answer ONLY from the provided document.
If the answer is not present, say so.

Respond in the same language as the user's query.
"""
            },
            {
                "role": "user",
                "content": f"""
Document data:
{doc_data}

User question:
{user_message}
"""
            }
        ],
        stream=True
    )

    for chunk in response:

        if not getattr(chunk, "choices", None):
            continue

        content = getattr(
            chunk.choices[0].delta,
            "content",
            None
        )

        if content:
            yield content

def generate_doc_data():
    try:
        with zipfile.ZipFile("/workspaces/bulbul/backend/output.zip", "r") as zip_ref:

            # check if file exists in zip
            if "document.html" not in zip_ref.namelist():
                raise FileNotFoundError(
                    "document.html not found inside zip"
                )

            # read html content
            with zip_ref.open("document.html") as html_file:
                html_content = html_file.read().decode("utf-8")

            # convert html -> text
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text(separator="\n", strip=True)

            doc_data = text
            logger.info("Document data extracted successfully")
            return doc_data
    except Exception as e:
        logger.error(f"Error extracting document data: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to extract document data")


@router.post("/chat", status_code=200)
async def chat(user_message: str):
    try:
        doc_data = generate_doc_data()
        return StreamingResponse(
            generate_chat_stream(
                user_message,
                doc_data
            ),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error processing chat completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat completion")