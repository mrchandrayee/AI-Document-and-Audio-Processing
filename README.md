# 🚀 AI Document and Audio Processing API

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

A powerful, scalable API for intelligent document and audio processing, leveraging OpenAI's advanced GPT and Whisper models to extract insights from your files.

## ✨ Features

### 📄 Document Analysis
- **Multi-format Processing:**
  - 🖼️ Images (PNG, JPEG, JPG)
  - 📝 Documents (PDF, DOCX, DOC, RTF, TXT)
  - 📊 Spreadsheets (XLSX, XLS)
- **Intelligent Content Analysis:**
  - Generate comprehensive summaries
  - Extract key insights and answer specific questions
  - Analyze complex content with GPT models
- **Flexible Response Formats:**
  - Multiple API versions with customizable outputs
  - String or PDF response options

### 🔊 Audio Processing
- **Advanced Transcription:**
  - High-accuracy audio transcription with OpenAI Whisper
  - Smart optimization for clear results
- **Intelligent Audio Analysis:**
  - Contextual understanding with GPT
  - Detailed insights from spoken content
- **Audio Enhancement:**
  - 🔇 Background noise removal
  - 🌍 Cross-language support with forced English translation

## 🛠️ Setup and Configuration

### 📋 Prerequisites

- Docker
- OpenAI API key
- 2GB+ RAM recommended for optimal performance

### 🔐 Environment Variables

1. Copy the `.env.example` file and rename it to `.env`:
   ```bash
   cp .env.example .env
   ```
   
2. Configure your environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   AUTH_SECRET_KEY=your_auth_secret_key
   ```

### 🐳 Running with Docker

```bash
# Build the Docker image
docker build . -t ai-processing-api:latest

# Run the container
docker container run -p 8000:8000 ai-processing-api
```

### 🔄 Health Check

Once running, verify the API is operational by accessing:
```
http://localhost:8000/
```
You should receive a success message indicating the backend is healthy.

## 🔌 API Endpoints

### 📝 Document Processing

<details>
<summary><b>Basic Chat Completion (v1)</b> - Text or PDF response</summary>

#### Endpoint
```
POST /v1/chat-completion
```

#### Request

```bash
curl --location 'http://localhost:8000/v1/chat-completion' \
--header 'Authorization: your_auth_secret_key' \
--form 'file=@"/path/to/document.pdf"' \
--form 'prompt="Summarize this document"' \
--form 'response_type="string"' \
--form 'model_name="gpt-4o-mini"'
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The document file (PDF, Image, Word, Excel, etc.) |
| `prompt` | String | Yes | Your instruction for analyzing the document |
| `response_type` | String | No | Response format: `string` or `pdf` (default: `string`) |
| `model_name` | String | No | OpenAI model: `gpt-4o` or `gpt-4o-mini` (default: `gpt-4o-mini`) |
| `sheet_names` | String | No | For Excel files, comma-separated sheet names |

</details>

<details>
<summary><b>JSON Response Format (v2)</b> - Structured JSON output</summary>

#### Endpoint
```
POST /v2/chat-completion
```

#### Request

```bash
curl --location 'http://localhost:8000/v2/chat-completion' \
--header 'Authorization: your_auth_secret_key' \
--form 'file=@"/path/to/document.pdf"' \
--form 'prompt="Summarize this document"' \
--form 'model_name="gpt-4o-mini"' \
--form 'temperature=0.7'
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The document file to analyze |
| `prompt` | String | Yes | Your instruction for analyzing the document |
| `model_name` | String | No | OpenAI model: `gpt-4o` or `gpt-4o-mini` (default: `gpt-4o-mini`) |
| `temperature` | Float | No | Model temperature (0.0-2.0) (default: 0.6) |

</details>

### 🔊 Audio Processing

<details>
<summary><b>Audio Transcription</b> - Convert speech to text</summary>

#### Endpoint
```
POST /audio-transcription
```

#### Request

```bash
curl --location 'http://localhost:8000/audio-transcription' \
--header 'Authorization: your_auth_secret_key' \
--form 'file=@"/path/to/audio.mp3"' \
--form 'remove_noise="true"' \
--form 'force_english="true"'
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Audio file (mp3, wav, ogg, m4a, flac) |
| `remove_noise` | Boolean | No | Apply noise removal (default: true) |
| `force_english` | Boolean | No | Force English transcription (default: true) |

</details>

<details>
<summary><b>Audio Analysis with GPT</b> - Intelligent audio content analysis</summary>

#### Endpoint
```
POST /audio-analysis
```

#### Request

```bash
curl --location 'http://localhost:8000/audio-analysis' \
--header 'Authorization: your_auth_secret_key' \
--form 'file=@"/path/to/audio.mp3"' \
--form 'prompt="Summarize the key points from this meeting"' \
--form 'remove_noise="true"' \
--form 'force_english="true"' \
--form 'model_name="gpt-4o"'
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Audio file to analyze |
| `prompt` | String | Yes | Analysis instructions for GPT |
| `remove_noise` | Boolean | No | Apply noise removal (default: true) |
| `force_english` | Boolean | No | Force English transcription (default: true) |
| `model_name` | String | No | OpenAI model to use (default: `gpt-4o-mini`) |

</details>

## 🎧 Audio Processing Features

<div align="center">
  <img src="https://img.shields.io/badge/Whisper-5A67D8?style=for-the-badge" alt="Whisper" />
  <img src="https://img.shields.io/badge/Audio_Processing-FF5A5F?style=for-the-badge" alt="Audio Processing" />
</div>

### 1️⃣ Noise Removal
Advanced audio pre-processing algorithms eliminate unwanted background elements:
- 🎵 Music interference
- 🎤 Background vocals and songs
- 🌧️ Ambient environmental noise

### 2️⃣ Force English Transcription
Intelligent language conversion that:
- 🌍 Detects source language automatically
- 🔄 Translates and transcribes into fluent English
- 📝 Maintains semantic meaning across languages

### 3️⃣ Advanced Audio Analysis
Powerful GPT-based processing for:
- 📊 Comprehensive meeting summaries
- 🔑 Extraction of key discussion points
- ❓ Answering specific questions about audio content
- 📈 Detailed content analysis and insights

## 📂 Supported File Formats

<div align="center">

| Category | Formats |
|:--------:|:-------:|
| 📝 **Documents** | PDF, DOCX, DOC, RTF, TXT |
| 🖼️ **Images** | PNG, JPEG, JPG |
| 📊 **Spreadsheets** | XLSX, XLS |
| 🎵 **Audio** | MP3, WAV, OGG, M4A, FLAC |

</div>

## 🔮 Future Development

<div align="center">
  <img src="https://img.shields.io/badge/Coming_Soon-34D399?style=for-the-badge" alt="Coming Soon" />
</div>

### 📦 Zip File Processing API
A powerful new endpoint for batch processing:
- Upload a single zip archive containing multiple files
- Receive individual summaries for each enclosed document
- **Limitations:**
  - Maximum zip file size: 20MB
  - Maximum number of files per archive: 20

---
