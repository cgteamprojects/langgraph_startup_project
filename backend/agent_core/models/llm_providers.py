import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# Load environment variables from .env file
load_dotenv()

# Get values from environment variables
azure_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")


def GetAzureOpenAIChatClient(model_capabilities=None):
    llm = AzureChatOpenAI(
                model=azure_model_name,
                azure_deployment=azure_deployment_name,
                api_version=azure_api_version,
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                model_kwargs=model_capabilities if model_capabilities else {},
                temperature=0
)
    return llm

# Initialize the LLM instance
llm = GetAzureOpenAIChatClient()

# Export the client creation function and the initialized instance
__all__ = ['GetAzureOpenAIChatClient', 'llm']