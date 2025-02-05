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
--form 'response_type="pdf"' \
--form 'model_name="gpt-4o-mini"'
```

`model_name` can be 'gpt-4o' or 'gpt-4o-mini'
`response_type` can be 'string' or 'pdf'

### TODO
- Fix image erros - it is throwing erros when images are served
- Input and output file shoule be optional
- Check if we can support rtf, xlsx, xls file extensions
> This needs excel parsing to make sure the rows and columns relationship is maintained in a way so that when we pass the raw data to the model it have the context about the table in excel.