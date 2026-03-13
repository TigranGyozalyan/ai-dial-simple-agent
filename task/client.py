import json
from typing import Any

import requests

from task.models.message import Message
from task.models.role import Role
from task.tools.base import BaseTool


class DialClient:

    def __init__(
            self,
            endpoint: str,
            deployment_name: str,
            api_key: str,
            tools: list[BaseTool] | None = None
    ):
        if not api_key:
            raise "api_key is required"
        self._endpoint = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions"
        self._api_key = api_key

        self._tools = tools

        self._tools_dict: dict[str, BaseTool] = { }
        for tool in tools:
            self._tools_dict[tool.name] = tool


    def get_completion(self, messages: list[Message], print_request: bool = True) -> Message:
        headers = {
            'api-key': self._api_key,
            'Content-Type': 'application/json',
        }
        request_data = {
            'messages': [msg.to_dict() for msg in messages],
            'tools': [t.schema for t in self._tools]
        }
        if print_request:
            print(self._endpoint)
            print("REQUEST:", json.dumps({"messages": [msg.to_dict() for msg in messages]}, indent=2))

        response = requests.post(self._endpoint, json=request_data, headers=headers)

        if not response.status_code == 200:
            raise Exception(response.json())

        result = response.json()
        choice = result.get('choices')[0]
        if print_request:
            print(f"response: {choice}")
        message_data = choice.get('message')
        content = message_data.get('content')
        tool_calls = message_data.get('tool_calls')
        ai_response = Message(role=Role.AI, content=content, tool_calls=tool_calls)

        if choice.get('finish_reason') == 'tool_calls':
            messages.append(ai_response)
            tool_messages = self._process_tool_calls(tool_calls)
            messages.extend(tool_messages)
            return self.get_completion(messages, print_request)
        return ai_response


    def _process_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[Message]:
        """Process tool calls and add results to messages."""
        tool_messages = []
        for tool_call in tool_calls:
            tool_call_id = tool_call.get('id')
            function = tool_call.get('function')
            name = tool_call.get('name')
            args = json.loads(function.get('arguments'))

            tool_execution_result = self._call_tool(function.get('name'), args)
            tool_messages.append(Message(role=Role.TOOL, name=name, tool_call_id= tool_call_id,content=tool_execution_result))
            print(f"FUNCTION '{function}'\n{tool_execution_result}\n{'-' * 50}")
        return tool_messages

    def _call_tool(self, function_name: str, arguments: dict[str, Any]) -> str:
        if not self._tools_dict[function_name]:
            return f"Unknown function: {function_name}"

        return self._tools_dict[function_name].execute(arguments)
