# Trading Idea Generator

A Gen AI-powered application that generates trading ideas based on market data and research using RAG(llamaIndex and OpenAI).

## Features

- PDF generation from extracted data
- Vector embeddings creation using LlamaIndex
- RESTful API endpoints for trading idea generation
- Scheduled background jobs for data processing
- Comprehensive logging system
- Parallel processing for optimal performance

## Sample output
![Sample Output](https://i.ibb.co/MsZDcCt/Output-trading.png)


## Tech Stack

- **FastAPI**: Modern web framework for building APIs
- **LlamaIndex**: For document processing and vector embeddings
- **OpenAI**: AI models for text processing and embeddings
- **APScheduler**: For scheduling background tasks
- **FPDF**: PDF generation
- **Python concurrent.futures**: Parallel processing
- **Logging**: Custom configured logging system


## Installation

1. Clone the repository:
```bash
git clone git@github.com:mohith2017/trading-idea-generator.git
cd trading-idea-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Set the `OPENAI_API_KEY` in the `.env` file.

4. Create vector embeddings: (This is only done once in the startup of the application)
- Download the JSON file directory and place them in the `src/data/downloaded_files/` directory.
- Unzip the data_dir.zip file in the `src/data/downloaded_files/` directory.


5. Run the application:
```bash
uvicorn src.main:app --reload
```
This automatically creates the vector embeddings and stores them in the `src/data/vector_store` directory. And starts the FastAPI server.

6. Test the API endpoints:
-   You can test the API endpoints using the FastAPI interactive API docs, which are available at `http://127.0.0.1:8000/docs`.

Or use `curl` or any other HTTP client to test the endpoints.
```bash
curl -X POST "http://127.0.0.1:8000/v1/generate" -H "Content-Type: application/json
```

## Testing
To run the tests, use the following command:
```bash
cd trading-idea-generator
python -m pytest tests/
```
