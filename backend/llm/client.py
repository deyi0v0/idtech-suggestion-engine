import os
import json
from openai import OpenAI
from typing import List, Dict, Any
from dotenv import load_dotenv
from .prompts import build_chat_prompt, TOOLS
from ..engine.rulesEngine.product_filtering import product_filtering
from ..db.session import SessionLocal
from ..engine.solution_schemas import RecommendationBundle

# Ensure environment variables are loaded
load_dotenv()

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def get_chat_response(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Orchestrates the flow: Text -> Params -> Tool Call -> Result -> Explanation -> JSON.
        """
        messages = build_chat_prompt(message, history)
       
        # First call to identify constraints and call tools
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if not tool_calls:
            return {"content": response_message.content} # just talk to user if no tool calls

        # Handle Tool Calls
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if function_name == "product_filtering":
                # Execute database filtering
                db = SessionLocal()
                try:
                    # product_filtering expects (db, constraints)
                    raw_results = product_filtering(db, args.get("constraints", {}))
                    content = json.dumps(raw_results)
                finally:
                    db.close()

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": content,
                })

        # Final call to generate the RecommendationBundle and Explanation
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        raw_json = json.loads(final_response.choices[0].message.content)

        # If it looks like a RecommendationBundle, validate it
        if "hardware_name" in raw_json:
            try:
                bundle = RecommendationBundle(**raw_json)
                return bundle.model_dump()
            except Exception:
                # Fallback to raw if validation fails
                return raw_json
        
        return raw_json

# Instantiate the client
_client_instance = LLMClient()

# Exported function for easy access
def get_chat_response(message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    return _client_instance.get_chat_response(message, history)
