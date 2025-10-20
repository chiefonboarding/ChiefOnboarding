import json
from datetime import time as datetime_time
from typing import Any, Dict, List, Optional

try:
    import openai
except ImportError:
    openai = None

from django.conf import settings
from django.contrib.auth import get_user_model

from admin.sequences.models import Condition, Sequence
from admin.to_do.models import ToDo
from users.models import User


class ChiefOnboardingAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        self.conversation_history = []
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_new_hire",
                    "description": "Create a new hire in the ChiefOnboarding system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "first_name": {
                                "type": "string",
                                "description": "First name of the new hire",
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Last name of the new hire",
                            },
                            "email": {
                                "type": "string",
                                "description": "Email address of the new hire",
                            },
                            "position": {
                                "type": "string",
                                "description": "Job position/title",
                            },
                            "start_day": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format",
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number (optional)",
                            },
                            "sequences": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of sequence IDs to assign",
                            },
                        },
                        "required": ["first_name", "last_name", "email"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_employees",
                    "description": "List all employees in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["newhire", "admin", "manager", "all"],
                                "description": "Filter by role",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_sequences",
                    "description": "List all available sequences/workflows",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_employee_details",
                    "description": "Get detailed information about a specific employee",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email of the employee",
                            }
                        },
                        "required": ["email"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_sequence_to_employee",
                    "description": "Assign a sequence to an employee",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Employee email",
                            },
                            "sequence_id": {
                                "type": "integer",
                                "description": "Sequence ID to add",
                            },
                        },
                        "required": ["email", "sequence_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_sequence",
                    "description": "Create a new onboarding or offboarding sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the sequence (e.g., 'Technical Onboarding for Mechanics')",
                            },
                            "category": {
                                "type": "string",
                                "enum": ["onboarding", "offboarding"],
                                "description": "Type of sequence: 'onboarding' for new hires or 'offboarding' for departures",
                            },
                        },
                        "required": ["name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add_todo_to_sequence",
                    "description": "Add a to-do task to a sequence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sequence_id": {
                                "type": "integer",
                                "description": "ID of the sequence to add the task to",
                            },
                            "task_name": {
                                "type": "string",
                                "description": "Name/title of the to-do task",
                            },
                            "task_content": {
                                "type": "string",
                                "description": "Detailed content/description of the task",
                            },
                            "due_on_day": {
                                "type": "integer",
                                "description": "Number of days after start date when task is due (e.g., 1 for first day, 7 for first week)",
                            },
                        },
                        "required": ["sequence_id", "task_name", "task_content", "due_on_day"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_sequence_details",
                    "description": "Get detailed information about a sequence including all its templates/blocks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sequence_id": {
                                "type": "integer",
                                "description": "ID of the sequence",
                            },
                        },
                        "required": ["sequence_id"],
                    },
                },
            },
        ]

    def create_new_hire(
        self,
        first_name: str,
        last_name: str,
        email: str,
        position: str = "",
        start_day: Optional[str] = None,
        phone: str = "",
        sequences: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        try:
            from organization.models import Organization

            org = Organization.object.get()

            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": get_user_model().Role.NEWHIRE,
                "position": position,
                "phone": phone,
                "timezone": org.timezone,
                "language": org.language,
            }

            if start_day:
                user_data["start_day"] = start_day
            else:
                user_data["start_day"] = org.current_datetime.date()

            user = User.objects.create(**user_data)

            if sequences:
                sequence_objs = Sequence.objects.filter(id__in=sequences)
                user.add_sequences(sequence_objs)

            return {
                "success": True,
                "message": f"Successfully created new hire: {user.full_name}",
                "user_id": user.id,
                "email": user.email,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_employees(self, role: str = "all") -> Dict[str, Any]:
        try:
            if role == "newhire":
                users = User.new_hires.all()
            elif role == "admin":
                users = User.objects.filter(role=User.Role.ADMIN)
            elif role == "manager":
                users = User.objects.filter(role=User.Role.MANAGER)
            else:
                users = User.objects.all()

            employees = [
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.get_role_display(),
                    "position": user.position,
                }
                for user in users[:50]
            ]

            return {
                "success": True,
                "employees": employees,
                "count": len(employees),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_sequences(self) -> Dict[str, Any]:
        try:
            sequences = Sequence.objects.all()
            sequence_list = [
                {"id": seq.id, "name": seq.name} for seq in sequences
            ]
            return {
                "success": True,
                "sequences": sequence_list,
                "count": len(sequence_list),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_employee_details(self, email: str) -> Dict[str, Any]:
        try:
            user = User.objects.get(email__iexact=email)
            return {
                "success": True,
                "employee": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.get_role_display(),
                    "position": user.position,
                    "phone": user.phone,
                    "start_day": str(user.start_day) if user.start_day else None,
                    "manager": user.manager.full_name if user.manager else None,
                    "buddy": user.buddy.full_name if user.buddy else None,
                },
            }
        except User.DoesNotExist:
            return {"success": False, "error": f"Employee with email {email} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_sequence_to_employee(
        self, email: str, sequence_id: int
    ) -> Dict[str, Any]:
        try:
            user = User.objects.get(email__iexact=email)
            sequence = Sequence.objects.get(id=sequence_id)

            user.add_sequences([sequence])

            return {
                "success": True,
                "message": f"Successfully added sequence '{sequence.name}' to {user.full_name}",
            }
        except User.DoesNotExist:
            return {"success": False, "error": f"Employee with email {email} not found"}
        except Sequence.DoesNotExist:
            return {"success": False, "error": f"Sequence with ID {sequence_id} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_sequence(self, name: str, category: str = "onboarding") -> Dict[str, Any]:
        try:
            category_map = {
                "onboarding": Sequence.Category.ONBOARDING,
                "offboarding": Sequence.Category.OFFBOARDING,
            }
            
            category_value = category_map.get(category.lower(), Sequence.Category.ONBOARDING)
            
            sequence = Sequence.objects.create(
                name=name,
                category=category_value,
                auto_add=False,
            )
            
            return {
                "success": True,
                "message": f"Successfully created {category} sequence: {sequence.name}",
                "sequence_id": sequence.id,
                "sequence_name": sequence.name,
                "category": category,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_todo_to_sequence(
        self, sequence_id: int, task_name: str, task_content: str, due_on_day: int
    ) -> Dict[str, Any]:
        try:
            sequence = Sequence.objects.get(id=sequence_id)
            
            todo = ToDo.objects.create(
                name=task_name,
                content=task_content,
                template=True,
                due_on_day=due_on_day,
            )
            
            condition = Condition.objects.create(
                sequence=sequence,
                condition_type=0,
                days=due_on_day,
                time=datetime_time(9, 0),
            )
            condition.to_do.add(todo)
            
            return {
                "success": True,
                "message": f"Successfully added to-do '{task_name}' to sequence '{sequence.name}' (due on day {due_on_day})",
                "todo_id": todo.id,
                "condition_id": condition.id,
            }
        except Sequence.DoesNotExist:
            return {"success": False, "error": f"Sequence with ID {sequence_id} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_sequence_details(self, sequence_id: int) -> Dict[str, Any]:
        try:
            sequence = Sequence.objects.get(id=sequence_id)
            conditions = sequence.conditions.all().order_by('days', 'time')
            
            blocks = []
            for condition in conditions:
                block_info = {
                    "day": condition.days,
                    "time": f"{condition.time}:00",
                    "type": condition.get_condition_type_display(),
                }
                
                if condition.to_do.exists():
                    block_info["todos"] = [
                        {"id": todo.id, "name": todo.name, "content": todo.content}
                        for todo in condition.to_do.all()
                    ]
                
                if condition.resources.exists():
                    block_info["resources"] = [
                        {"id": r.id, "name": r.name}
                        for r in condition.resources.all()
                    ]
                
                if condition.admin_tasks.exists():
                    block_info["admin_tasks"] = [
                        {"id": t.id, "name": t.name}
                        for t in condition.admin_tasks.all()
                    ]
                
                blocks.append(block_info)
            
            return {
                "success": True,
                "sequence": {
                    "id": sequence.id,
                    "name": sequence.name,
                    "category": sequence.get_category_display(),
                    "blocks_count": len(blocks),
                    "blocks": blocks,
                },
            }
        except Sequence.DoesNotExist:
            return {"success": False, "error": f"Sequence with ID {sequence_id} not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        function_map = {
            "create_new_hire": self.create_new_hire,
            "list_employees": self.list_employees,
            "list_sequences": self.list_sequences,
            "get_employee_details": self.get_employee_details,
            "add_sequence_to_employee": self.add_sequence_to_employee,
            "create_sequence": self.create_sequence,
            "add_todo_to_sequence": self.add_todo_to_sequence,
            "get_sequence_details": self.get_sequence_details,
        }

        if function_name not in function_map:
            return json.dumps({"error": f"Unknown function: {function_name}"})

        try:
            result = function_map[function_name](**arguments)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def chat(self, message: str) -> str:
        self.conversation_history.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant for ChiefOnboarding, an employee onboarding system. 
                    You can help users manage employees, create new hires, assign sequences, and more.
                    
                    When executing actions:
                    - Always confirm what you're about to do before executing
                    - Provide clear feedback on success or failure
                    - Be helpful and professional
                    - If you need more information, ask the user
                    """,
                }
            ]
            + self.conversation_history,
            tools=self.tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                }
            )

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                function_response = self._execute_function(function_name, arguments)

                self.conversation_history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response,
                    }
                )

            second_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant for ChiefOnboarding. 
                        Provide clear, helpful responses based on the function results.""",
                    }
                ]
                + self.conversation_history,
            )

            final_message = second_response.choices[0].message.content
            self.conversation_history.append(
                {"role": "assistant", "content": final_message}
            )
            return final_message
        else:
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message.content}
            )
            return assistant_message.content

    def reset_conversation(self):
        self.conversation_history = []
