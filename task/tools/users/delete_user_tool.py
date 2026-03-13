from typing import Any

from task.tools.users.base import BaseUserServiceTool


class DeleteUserTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        return 'delete_user'

    @property
    def description(self) -> str:
        return 'Tool for deleting users'

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
          "type": "object",
          "properties": {
            "id": {
              "type": "number",
              "description": "ID of the user to delete"
            }
          },
          "required": [
            "id"
          ]
        }

    def execute(self, arguments: dict[str, Any]) -> str:
        try:
            user_id = int(arguments["id"])
            return self._user_client.delete_user(user_id)
        except Exception as e:
            return f"Error while deleting user: {str(e)}"