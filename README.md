# Bulbul — Document Assistant

Bulbul is a basic multilingual document assistant that lets you upload a PDF, ask questions about it in any Indian language, and listen to the answers read aloud.
The aim of this project was to explore the Sarvam APIs. This project uses only sarvam APIs for LLM capabilities.

## How it works

1. **Upload** — Upload a PDF document and select its language. The document is processed using Sarvam's Document Intelligence API to extract clean text.
2. **Chat** — Ask questions about the document in any supported language (English, Hindi, Telugu, Tamil, etc.). Bulbul answers using only the content of the uploaded document.
3. **Read Aloud** — Any answer can be played back as speech using text-to-speech, with the correct voice for the detected language.
4. **Voice Input** — Questions can also be spoken via the microphone, transcribed using speech-to-text, and answered automatically.

---

## Sarvam APIs Used

| API                                                         | Purpose                                                      |
| ----------------------------------------------------------- | ------------------------------------------------------------ |
| **Document Intelligence** (`document_intelligence`)         | Converts uploaded PDFs to structured HTML/text               |
| **Language Identification** (`text.identify_language`)      | Detects the language of the answer to convert text to speech |
| **Chat Completions** (`chat.completions` — `sarvam-105b`)   | Answers questions from document content                      |
| **Text-to-Speech** (`text_to_speech.convert` — `bulbul:v3`) | Reads answers aloud in the correct language                  |
| **Speech-to-Text** (`speech_to_text`)                       | Transcribes voice questions from the microphone              |

---

## Running Locally

### Prerequisites

- Python 3.11 or 3.12
- [Poetry](https://python-poetry.org/docs/#installation)
- A [Sarvam AI](https://www.sarvam.ai/) API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/varshapateliitdh/bulbul.git
   cd bulbul
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Create a `.env` file** in the project root:
   ```env
   SARVAM_API_KEY=your_api_key_here
   ```

4. **Run the server**
   ```bash
   poetry run python main.py
   ```

5. **Open the app**

   Open `frontend/index.html` in your browser, or serve it via any static file server. The backend runs at `http://localhost:8000`.

---

## Project Structure

```
bulbul/
├── main.py                  # FastAPI app entry point
├── backend/
│   ├── upload_file.py       # PDF upload & document intelligence
│   ├── chat.py              # Chat completions
│   ├── read_aloud.py        # Text-to-speech + language detection
│   ├── talk.py              # Speech-to-text (voice input)
│   └── doc_utils.py         # Document storage utilities
├── frontend/
│   ├── index.html           # UI
│   ├── app.js               # Frontend logic
│   └── style.css            # Styling
└── uploads/                 # Temporarily stored document text
```

[Demo Recording](./bulbul_demo.mp4)

---

## Findings & Limitations

### `sarvam-105b` — Language Instruction Following

**Scenario:** Document text is in Hindi (or any Indian language). User asks a question in English. The system prompt instructs the model to detect the question language and respond in the same language.

**Finding:** The model consistently ignored the language instruction and responded in the language of the document, not the question. This held true even with explicit, step-by-step chain-of-thought prompting:

```python
response = client.chat.completions(
    model="sarvam-105b",
    messages=[
        {
            "role": "system",
            "content": """
You are a document assistant.

Answer ONLY from the provided document.
If the answer is not present, say so.

Plan of action:
1) Analyse the Document data to understand its content and structure. Detect the language of the document.
2) Analyse the User question to understand what is being asked. Detect the language of the question.
3) Come up with the answer for the question
4) Translate the answer to the same language as the question.

Remember to follow the plan of action step by step, and ensure that the final answer is in the same
language as the user's question.
"""
        },
        {
            "role": "user",
            "content": f"Document data:\n{doc_data}\n\nUser question:\n{user_message}"
        }
    ]
)
```

**Root Cause:** `sarvam-105b` is optimised for Indian languages and appears to have a strong prior toward the dominant language in the context window (i.e. the document). It does not reliably follow cross-lingual output instructions.

**Workaround:** Detect the question language independently using `text.identify_language`, let the LLM answer freely (it will answer in the document language), then post-process the answer through `text.translate` (`mayura:v1`) to the target language. This gives reliable results since translation is handled by a dedicated model rather than relying on the LLM's instruction-following.