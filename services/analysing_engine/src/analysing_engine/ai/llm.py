# from google.adk.agents import Agent
# from google.adk.runners import Runner
# from google.adk.models.lite_llm import LiteLlm

# from ..config import config
# from .prompt import PROMPT_TEMPLATE

# class CustomAsyncAgent:
#     def __init__(self):
#         self.agent = Agent(
#             name="pazyr_analysing_agent",
#             description="pazyr analysing agent",
#             model= LiteLlm(
#                 model=config.ai.llm.model,
#                 api_base=config.ai.llm.endpoint,
#                 api_key=config.ai.llm.api_key
#             ),
#             instruction="You are a Agent to analyse the given text and predict if the data is incliened towards users intrest."
#         )
#         self.runner = Runner(
#             app_name=config.service_name,
#             agent=self.agent
#         )

#     async def run(self, query: str):
#         prompt = PROMPT_TEMPLATE + query

#         session = await self.runner.session_service.create_session(
#             app_name=config.service_name
#         )

#         response = await self.runner.run_async(
#             user_id=config.service_name,
#             session_id=session.id
#         )

#         return response

#     async def run_stream(self, query: str):
#         prompt = PROMPT_TEMPLATE + query

#         session = await self.runner.session_service.create_session(
#             app_name=config.service_name
#         )

#         for chunk in await self.runner.run_async(
#             user_id=config.service_name,
#             session_id=session.id,
#             new_message=prompt

#         ):
#             yield chunk



from abc import ABC, abstractmethod

from litellm import acompletion
from pydantic import BaseModel

from ..config import config
from .prompt import PROMPT_TEMPLATE


class LLMRequest(BaseModel):
    system_prompt: str | None = None
    prompt: str
    temperature: float = 0.0

class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        pass


class LiteLLMProvider(LLMProvider):
    def __init__(
        self,
        provider: str,
        model: str, 
        endpoint: str | None = None, 
        api_key: str | None = None
    ):
        self.provider = provider
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key

    async def generate(self, request: LLMRequest) -> LLMResponse:
        messages = []
        
        if request.system_prompt:
            messages.append({
				"role": "system",
				"content": request.system_prompt
			})
        
        messages.append({
                "role": "user",
                "content": request.prompt
        })
        
        response = await acompletion(
            model = f"{self.provider}/{self.model}",
            api_base = self.endpoint,
            api_key = self.api_key,
            temperature = request.temperature,
            messages = messages
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model
        )

class LLMProviderFactory:
    @staticmethod
    def create(provider, model, endpoint, api_key) -> LLMProvider:
        return LiteLLMProvider(provider, model, endpoint, api_key)