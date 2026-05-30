# Bulbul — Document Assistant

Bulbul is a multilingual document assistant that lets you upload a PDF, ask questions about it in any Indian language, and listen to the answers read aloud.

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
