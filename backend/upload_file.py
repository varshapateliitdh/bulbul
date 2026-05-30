import ssl
import httpx
import zipfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
import tempfile
import asyncio
from dotenv import load_dotenv
from sarvamai import SarvamAI
from bs4 import BeautifulSoup
import uuid
from backend.doc_utils import UPLOADS_DIR, cleanup_expired_uploads

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


def generate_doc_data(file_path: str):
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:

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
            filename = f"doc_data_{uuid.uuid4().hex}.txt"
            with open(os.path.join(UPLOADS_DIR, filename), "w", encoding="utf-8") as f:
                f.write(doc_data)
            return filename

    except Exception as e:
        logger.error(f"Error extracting document data: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to extract document data")

@router.post("/upload-file", status_code=200)
async def get_copilot_result(file: UploadFile = File(...), language_code: str = None):
    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"document_{uuid.uuid4().hex}.pdf")
        output_zip_path = os.path.join(tmpdir, f"output_{uuid.uuid4().hex}.zip")
        result = {}

        try:
            contents = await file.read()
            with open(input_path, "wb") as f:
                f.write(contents)
            logger.info("File saved successfully")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")

        def process_document():
            # Create a document intelligence job
            job = client.document_intelligence.create_job(
                output_format="html",
                language=language_code
            )
            logger.info(f"Job created: {job.job_id}")

            job.upload_file(input_path)
            logger.info("File uploaded")

            job.start()
            logger.info("Job started")

            status = job.wait_until_complete()
            logger.info(f"Job completed with state: {status.job_state}")

            metrics = job.get_page_metrics()
            logger.info(f"Page metrics: {metrics}")

            job.download_output(output_zip_path)
            logger.info("Output zip saved")

            with zipfile.ZipFile(output_zip_path, "r") as zf:
                html_filename = next(
                    (n for n in zf.namelist() if n.endswith(".html")), None
                )
                if not html_filename:
                    raise ValueError("No HTML file found in output zip")
                logger.info(f"Extracted {html_filename} from zip")
                result["doc_filename"] = generate_doc_data(output_zip_path)

        try:
            await asyncio.get_event_loop().run_in_executor(None, process_document)
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise HTTPException(
                status_code=500, detail="Document processing failed")

        # Clean up expired uploads
        cleanup_expired_uploads()

        return JSONResponse(content={"doc_filename": result["doc_filename"]}, status_code=200)
