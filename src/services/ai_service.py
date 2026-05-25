from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import httpx
from typing import Optional, Dict, Any
import json
from fastapi import HTTPException
from src.api_schemas.ai import LLMRequestParams, LLMResponse

load_dotenv() 

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")


class ApiLLMService:
    """Сервис для интеграции с API LLM"""
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        """
        Инициализация сервиса
        Args:
            api_key: API ключ
            base_url: Базовый URL API
        """
        self.api_key = api_key
        self.base_url = base_url    # URL Модели
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=60.0,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",  # Ваш локальный адрес
                "X-Title": "Poll App (Development)"
            }
        )

        # Кэш для проверки поддержки tool calling
        self._tools_cache: Dict[str, bool] = {}
    
    async def _supports_tool_calling(self, model: str) -> bool:
        """
        Проверяет, поддерживает ли модель tool calling 
        Args:
            model: Название модели
        Returns:
            bool: True если модель поддерживает tool calling
        """
        # Проверяем кэш
        if model in self._tools_cache:
            return self._tools_cache[model]
        
        # Для openrouter/free всегда возвращаем False, так как роутер может переключиться на неподдерживающую модель
        if model == "openrouter/free":
            self._tools_cache[model] = False
            return False
        
        # Создаем отдельный клиент для проверки
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/models")
                
                if response.status_code == 200:
                    models_data = response.json()
                    
                    for m in models_data.get("data", []):
                        if m.get("id") == model:
                            supported_params = m.get("supported_parameters", [])
                            supports = "tools" in supported_params and "tool_choice" in supported_params
                            self._tools_cache[model] = supports
                            return supports
                    
                    # Если модель не найдена в списке, предполагаем что не поддерживает
                    self._tools_cache[model] = False
                    return False
        except Exception as e:
            print(f"Error checking tool calling support for {model}: {e}")  
        # По умолчанию возвращаем False для безопасности
        return False

    

    async def generate_response(
        self,
        params: LLMRequestParams,
        system_prompt: Optional[str] = None,
        timeout: int = 60
    ) -> LLMResponse:
        """
        Отправка запроса к LLM        
        Args:
            params: Параметры запроса
            system_prompt: Системный промпт
            timeout: Таймаут запроса в секундах           
        Returns:
            LLMResponse: Ответ от модели
        """
        # Формируем сообщения для API
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": params.prompt
        })

        try:
            # Подготавливаем тело запроса
            request_body = {
                "model": params.model,
                "messages": messages,
                "temperature": params.temperature,
                "max_tokens": params.max_tokens,
                "top_p": params.top_p,
                "frequency_penalty": params.frequency_penalty,
                "presence_penalty": params.presence_penalty,
            }
            
            # Добавляем опциональные параметры
            opt_params = ["stop","response_format","seed","top_k","repetition_penalty"]
            for param in opt_params:
                value = getattr(params, param, None)
                if value is not None:
                    request_body[param] = value

            # Проверяем, поддерживает ли модель tool calling
            use_tools = await self._supports_tool_calling(params.model)
            if use_tools and params.response_model is not None:
                # if not params.response_model:
                #     raise ValueError("response_model должна быть указана")
                
                # Добавляем параметры для tool calling
                tool_schema = {
                    "type": "function",
                    "function": params.response_model.model_json_schema()
                }
                request_body["tools"] = [tool_schema]
                request_body["tool_choice"] = {
                    "type": "function",
                    "function": {"name": params.response_model.__name__}
                }
                # Отправляем запрос с таймаутом
                response = await self.client.chat.completions.create(**request_body, timeout=timeout)
                # Извлекаем данные из tool_calls
                tool_call = response.choices[0].message.tool_calls[0]
                arguments_json = tool_call.function.arguments
                # Парсим JSON
                arguments_dict = json.loads(arguments_json)
                # Валидируем через Pydantic модель
                structured_obj = params.response_model(**arguments_dict)

                return LLMResponse(
                    content=None,
                    model=response.model,
                    finish_reason=response.choices[0].finish_reason,
                    usage=response.usage.model_dump() if response.usage else {},
                    structured_data=structured_obj
                )
            else:
                # Отправляем запрос
                response = await self.client.chat.completions.create(**request_body, timeout=timeout)
                    
                return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                usage=response.usage.model_dump() if response.usage else {}
            )
        except Exception as e:
            # Обработка ошибок от OpenAI клиента
            error_msg = str(e)         
            if "timeout" in error_msg.lower():
                raise HTTPException(
                    status_code=504,
                    detail=f"LLM request timeout after {timeout} seconds"
                )
            elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail=f"OpenRouter authentication failed: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"LLM request failed: {error_msg}"
                )
        
    
    async def generate_ai(
        self,
        params: LLMRequestParams,
        system_prompt: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Генерация JSON ответа от LLM   
        Args:
            params: Параметры запроса
            system_prompt: Системный промпт
            timeout: Таймаут запроса     
        Returns:
            Dict[str, Any]: Распарсенный JSON ответ
        """
        # Принудительно запрашиваем JSON формат
        
        response = await self.generate_response(params, system_prompt, timeout)
        if params.response_format == {"type": "json_object"}:
            # Парсим JSON из ответа
            try:
                # Пробуем найти JSON в ответе, если он обернут в другие символы
                content = response.content.strip()       
                # Удаляем markdown code blocks если есть
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3] 
                content = content.strip()

                # Парсим JSON
                json_data = json.loads(content)
                return json_data
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка в парсинге ответа как JSON: {str(e)}. Ожидался JSON, получено: {response.content}"
                )
        else:
            return response.content



# Функция для создания экземпляра сервиса
def get_llm_service(api_key: str = openrouter_api_key) -> ApiLLMService:
    """
    Фабрика для создания сервиса LLM
    """
    return ApiLLMService(api_key=api_key)