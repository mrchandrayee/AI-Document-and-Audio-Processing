from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import openai
from dotenv import load_dotenv
from pypdf import PdfReader
from typing import Annotated
from docx import Document
import base64
import tempfile
from enum import Enum
from markdown_pdf import MarkdownPdf, Section
from striprtf.striprtf import rtf_to_text
import pandas as pd
import os
from .util import parseDocuments
from .system_prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_V2
import requests
import json
from pydantic import BaseModel

class ResponseSchema(BaseModel):
    response: str
    file_response: str

load_dotenv(override=True)
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")

app = FastAPI()
client = openai.OpenAI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from your frontend domain
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class ResponseType(str, Enum):
    pdf = "pdf"
    string = "string"

class ModelType(str, Enum):
    gpt4o = "gpt-4o"
    gpt4omini = "gpt-4o-mini"

MODEL = 'gpt-4o'
SUPPORTED_EXTENSIONS = set(
    ['doc', 'dot', 'docx', 'dotx', 'docm', 'dotm', 'pdf', 'png', 'jpeg', 'jpg', 'rtf', 'xlsx', 'xls', 'txt'])

# Health checkup end point
@app.get("/")
def health():
    return {
        "status": "success",
        "message": "Backend Healthy"
    }

# Chat completion end point
@app.post("/v1/chat-completion")
def chatCompletion(prompt: Annotated[str, Form()], response_type: Annotated[ResponseType, Form()] = ResponseType.string, model_name: Annotated[ModelType, Form()] = ModelType.gpt4omini, file: Annotated[UploadFile | None, File()] = None, sheet_names: Annotated[str | None, Form()] = None, authorization: Annotated[str | None, Header()] = None):
    MODEL = model_name
    documentText = ''
    b64 = None

    if not authorization or (authorization != AUTH_SECRET_KEY):
        print(f"Authorization header: {authorization}")
        raise HTTPException(
            status_code=401, detail="Provide the correct authorization token in headers")

    if file is not None:
        fileExt = file.filename.split('.')[-1].lower()
        if fileExt not in SUPPORTED_EXTENSIONS:
            raise HTTPException(400, f"{fileExt} file type not supported")
        if fileExt == 'pdf':
            reader = PdfReader(file.file)
            for page in reader.pages:
                extracted_text = page.extract_text(extraction_mode='layout')
                if len(extracted_text.strip()) == 0:
                    extracted_text = page.extract_text()
                documentText += extracted_text
                documentText += '\n\n'
            if len(documentText.strip()) == 0:
                raise HTTPException(
                    status_code=400, detail="Unable to parse text from the given document or the document does not contain any text.")
        elif fileExt in ['png', 'jpeg', 'jpg']:
            with tempfile.TemporaryDirectory() as temp_dir:
                path = f"{temp_dir}/filename.{fileExt}"
                with open(path, 'wb') as img:
                    img.write(file.file.read())
                with open(path, 'rb') as img:
                    b64 = base64.b64encode(img.read()).decode("utf-8")
        elif fileExt in ['rtf']:
            documentText = rtf_to_text(file.file.read().decode('utf-8'))
        elif fileExt in ['xls', 'xlsx']:
            try:
                excelDF = None
                if sheet_names is None or len(sheet_names) == 0:
                    excelDF = pd.read_excel(file.file)
                    documentText = excelDF.to_string()
                else:
                    sheet_name_arr = list(map(lambda x: x.strip(), sheet_names.split(',')))
                    excelDF = pd.read_excel(file.file, sheet_name=sheet_name_arr)
                    if not isinstance(excelDF, dict):
                        raise HTTPException(400, "Something went wrong while parsing the excel sheet")
                    for key in excelDF:
                        documentText += f'Sheet Name: {key}\n\n'
                        documentText += excelDF[key].to_string()
                        documentText += '\n\n'
            except Exception as exp:
                print(exp)
                raise HTTPException(400, "Worksheet name not found")
        elif fileExt == 'txt':
            documentText += file.file.read().decode('utf-8')
        else:
            document = Document(file.file)
            for paragraph in document.paragraphs:
                documentText += paragraph.text if paragraph and paragraph.text else ""
            # text = ''
            # for elem in document.tables:
            #     textRow = set()
            #     for i, row in enumerate(elem.columns):
            #         for cell in row.cells:
            #             textRow.add(f"{cell.text}\n")
            #     text += f"{' '.join(list(textRow))}\n\n"
            # print(text)
    userContent = [
        {
            "type": "text",
            "text": ""
        }
    ]

    if len(documentText) > 0:
        userContent[0]['text'] = f"User prompt:\n{prompt}\n\nThis is document content: \n{documentText}"
    elif b64 is not None:
        userContent[0]['text'] = "I will be attaching an image"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": userContent
        }
    ]

    if file is None:
        messages = messages[1:]
        userContent[0]['text'] = prompt

    if b64 is not None:
        userContent.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    if response_type is ResponseType.pdf:
        pdf = MarkdownPdf(toc_level=2)
        content = response.choices[0].message.content
        # while breakWords <= len(content):
        pdf.add_section(Section(content))
        #     print(offset)
        #     breakWords+=offset
        pdf.save(f"response.pdf")
        return FileResponse(f"response.pdf",
                            media_type="application/pdf")

    return {
        "status": "success",
        "prompt": prompt,
        "response": response.choices[0].message.content
    }

@app.post("/v2/chat-completion")
def chatCompletionV2(prompt: Annotated[str, Form()], model_name: Annotated[ModelType, Form()] = ModelType.gpt4omini, file: Annotated[UploadFile | None, File()] = None, sheet_names: Annotated[str | None, Form()] = None, authorization: Annotated[str | None, Header()] = None, temperature: Annotated[float, Form()] = 0.6):
    if temperature < 0 or temperature > 2:
        raise HTTPException(
            status_code=400, detail="Temperature value is invalid. 0 <= temperature <= 2"
        )
    if not authorization or (authorization != AUTH_SECRET_KEY):
        print(f"Authorization header: {authorization}")
        raise HTTPException(
            status_code=401, detail="Provide the correct authorization token in headers")
    
    MODEL = model_name
    documentText, b64, _ = parseDocuments(file, sheet_names)
    userContent = [
        {
            "type": "text",
            "text": ""
        }
    ]

    if len(documentText) > 0:
        userContent[0]['text'] = f"User prompt:\n{prompt}\n\nThis is document content: \n{documentText}"
    elif b64 is not None:
        userContent[0]['text'] = "I will be attaching an image"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_V2
        },
        {
            "role": "user",
            "content": userContent
        }
    ]

    if file is None:
        userContent[0]['text'] = prompt

    if b64 is not None:
        userContent.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    response = {}
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature
        )
    except openai.RateLimitError as e:
        print(f"Rate limit error occurred: {e}")
        raise HTTPException(
            status_code=429, detail="OpenAI token limit exceeded")

    res_content = response.choices[0].message.content
    content = json.loads(res_content)
    print(content)
    download_link = None

    if ("file_response" in content) and content['file_response'] is not None:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(content['file_response']))
        pdf.save(f"response.pdf")

        files=[
            ('file',('response.pdf',open('response.pdf','rb'),'application/pdf'))
        ]
        upload_response = requests.request("POST", "https://tmpfiles.org/api/v1/upload", files=files).json()
        pdf_url:str = upload_response['data']['url']
        download_link = "https://tmpfiles.org" + "/dl/" + '/'.join(pdf_url.split("/")[-2:])

    return {
        "status": "success",
        "prompt": prompt,
        "response": content['response'],
        "pdf": download_link
    }

@app.post("/v3/chat-completion")
def chatCompletionV3(prompt: Annotated[str, Form()], model_name: Annotated[ModelType, Form()] = ModelType.gpt4omini, file: Annotated[UploadFile | None, File()] = None, sheet_names: Annotated[str | None, Form()] = None, authorization: Annotated[str | None, Header()] = None, temperature: Annotated[float, Form()] = 0.6):
    if temperature < 0 or temperature > 2:
        raise HTTPException(
            status_code=400, detail="Temperature value is invalid. 0 <= temperature <= 2"
        )
    if not authorization or (authorization != AUTH_SECRET_KEY):
        print(f"Authorization header: {authorization}")
        raise HTTPException(
            status_code=401, detail="Provide the correct authorization token in headers")
    
    MODEL = model_name
    documentText, b64, base64_urls = parseDocuments(file, sheet_names, True)
    userContent = [
        {
            "type": "text",
            "text": ""
        }
    ]

    if len(documentText) > 0:
        userContent[0]['text'] = f"User prompt:\n{prompt}\n\nThis is document content: \n{documentText}"
    elif b64 is not None:
        userContent[0]['text'] = "I will be attaching an image"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_V2
        },
        {
            "role": "user",
            "content": userContent
        }
    ]

    if file is None:
        userContent[0]['text'] = prompt

    if b64 is not None:
        userContent.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    if len(base64_urls) > 0:
        for url in base64_urls:
            userContent.append({
                "type": "image_url",
                "image_url": {"url": url, "detail": "low"},
            })

    response = {}
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature
        )
    except openai.RateLimitError as e:
        print(f"Rate limit error occurred: {e}")
        raise HTTPException(
            status_code=429, detail="OpenAI token limit exceeded")

    res_content = response.choices[0].message.content
    content = json.loads(res_content)
    print(content)
    download_link = None

    if ("file_response" in content) and content['file_response'] is not None:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(content['file_response']))
        pdf.save(f"response.pdf")

        files=[
            ('file',('response.pdf',open('response.pdf','rb'),'application/pdf'))
        ]
        upload_response = requests.request("POST", "https://tmpfiles.org/api/v1/upload", files=files).json()
        pdf_url:str = upload_response['data']['url']
        download_link = "https://tmpfiles.org" + "/dl/" + '/'.join(pdf_url.split("/")[-2:])

    return {
        "status": "success",
        "prompt": prompt,
        "response": content['response'],
        "pdf": download_link
    }