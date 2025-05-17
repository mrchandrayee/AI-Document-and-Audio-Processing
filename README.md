# ff-poc
POC for document (Image, PDF, Word doc) summary and audio transcription

### Environment variables

First, copy the `.env.example` file and rename it as `.env`..
Add OpenAI API key in `.env` file at the root directory. As `OPENAI_API_KEY`.


### To run the docker container:

1. Build the image by `docker build . -t test-model:latest`
2. Run the container `docker container run -p 8000:8000 test-model`


### Request cURL

```
curl --location 'http://localhost:8000/chat-completion' \
--form 'file=@"/Users/ayushagrawal/Downloads/pexels-huynhthanhphong-6864554.jpg"' \
--form 'prompt="What is happening in the image provided"' \
--form 'response_type="string"' \
--form 'model_name="gpt-4o-mini"'
```

`model_name` can be 'gpt-4o' or 'gpt-4o-mini'
`response_type` can be 'string' or 'pdf'
`sheet_names` can be specified for excel documents, these are string of values seperated by commas. Note: If calling this API from postman don't include quotes as it can break things. If not specified the API will use the first sheet.

### Audio Transcription

The service now supports audio transcription with Whisper model optimization:

```
curl --location 'http://localhost:8000/audio-transcription' \
--form 'file=@"/path/to/audio.mp3"' \
--form 'remove_noise="true"' \
--form 'force_english="true"'
```

#### Audio Transcription Features:

1. **Noise Removal**: Pre-processes audio to eliminate background elements such as:
   - Music
   - Songs
   - Ambient noise

2. **Force English Transcription**: Configures Whisper to return transcriptions in English, regardless of input language.

3. **Audio Analysis with GPT**: Combines transcription with GPT analysis:

```
curl --location 'http://localhost:8000/audio-analysis' \
--form 'file=@"/path/to/audio.mp3"' \
--form 'prompt="Summarize the key points from this meeting"' \
--form 'remove_noise="true"' \
--form 'force_english="true"' \
--form 'model_name="gpt-4o"'
```

Supported audio formats: mp3, wav, ogg, m4a, flac

## TO DO
1. A new API that takes a zip file and summarise each file in it. The upper limit of file would be 20MB. The max no. of files inside it can be 20 for now.
