# ff-poc
POC for document (Image, PDF, Word doc) summary

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

## TO DO
1. A new API that takes a zip file and summarise each file in it. The upper limit of file would be 20MB. The max no. of files inside it can be 20 for now.
