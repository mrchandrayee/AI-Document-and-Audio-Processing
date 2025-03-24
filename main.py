from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
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

load_dotenv(override=True)
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")

app = FastAPI()
client = openai.OpenAI()

class ResponseType(str, Enum):
    pdf = "pdf"
    string = "string"

class ModelType(str, Enum):
    gpt4o = "gpt-4o"
    gpt4omini = "gpt-4o-mini"

MODEL = 'gpt-4o'
SUPPORTED_EXTENSIONS = set(
    ['doc', 'dot', 'docx', 'dotx', 'docm', 'dotm', 'pdf', 'png', 'jpeg', 'jpg', 'rtf', 'xlsx', 'xls'])
SYSTEM_PROMPT = "You are an assistant who analysis documents provided which are of type image, pdf or word. The pdf and word document will be given to after extracting the text from them.\nThe document content will be specified by a different heading for you to differentiate between the document content and user prompt.\nIgnore all the formatting, spacing issues and line breaks, do not bring it up to the user or in the final response and correct them silently yourself.\nYou will give your response in beautiful and structured markdown unless specified explicitly."

# Health checkup end point
@app.get("/")
def health():
    return {
        "status": "success",
        "message": "Backend Healthy"
    }

# Chat completion end point
@app.post("/chat-completion")
def chatCompletion(prompt: Annotated[str, Form()], response_type: Annotated[ResponseType, Form()] = ResponseType.string, model_name: Annotated[ModelType, Form()] = ModelType.gpt4omini, file: Annotated[UploadFile | None, File()] = None, sheet_names: Annotated[str | None, Form()] = None, authorization: Annotated[str | None, Header()] = None):
    MODEL = model_name
    documentText = ''
    b64 = None

    if not authorization == AUTH_SECRET_KEY:
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
                documentText += page.extract_text(extraction_mode='layout')
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

    if file is None:
        userContent[0]['text'] = prompt

    if b64 is not None:
        userContent.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": userContent
            }
        ]
    )
    print(response.choices[0].message.content)

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
