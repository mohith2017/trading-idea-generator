import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine.router_query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from dotenv import load_dotenv
from ....utils.logger_config import logger

router = APIRouter()
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger = logger(__name__, 'app.log', level='DEBUG')


class GenerateResponse(BaseModel):
    generated_output: str

@router.post("/generate", response_model=GenerateResponse)
async def generate_trade_idea():
    try:
        logger.info("Starting trade idea generation")
        logger.info("Loading vector index from storage")
        storage_context = StorageContext.from_defaults(persist_dir="src/data/vector_store")
        vector_index = load_index_from_storage(storage_context)
        logger.debug("Loaded vector index from storage")

        vector_query_engine = vector_index.as_query_engine()
        vector_tool = QueryEngineTool.from_defaults(
                query_engine=vector_query_engine,
                description=(
                    "Useful for retrieving specific context from the trading data."
            ),
        )
        logger.debug("Created vector query engine and tool")

        query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[
                vector_tool,
            ],
            verbose=True
        )
        logger.debug("Initialized router query engine")

        prompt = "Generate a trading idea(long/short) based on the given data"
        logger.info(f"Executing query with prompt: {prompt}")
        response = query_engine.query(prompt)
        logger.info("Successfully generated trade idea")

        return GenerateResponse(generated_output=str(response))

    except Exception as e:
        logger.error(f"Error generating trade idea: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating trade idea: {str(e)}")
