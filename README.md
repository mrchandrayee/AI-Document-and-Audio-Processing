# AI
POC for document (Image, PDF, Word doc) summary

### Environment variables

First, copy the `.env.example` file and rename it as `.env`..
Add OpenAI API key in `.env` file at the root directory. As `OPENAI_API_KEY`.


### To run the docker container:

1. Build the image by `docker build . -t test-model:latest`
2. Run the container `docker container run -p 8000:8000 test-model`


### Request cURL

```
curl --location 'localhost:8000/chat-completion' \
--form 'file=@"/path/to/file"' \
--form 'prompt="Summerize the given document and include as much detail as possible."'
```
