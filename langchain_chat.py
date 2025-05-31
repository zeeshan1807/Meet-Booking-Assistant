from langchain.agents import Tool, initialize_agent
from langchain.tools import StructuredTool
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from datetime import datetime
import os
from calendar_integrations import get_available_slots_on_calender, book_slot_on_calendar

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    os.environ['OPENAI_API_KEY'] = api_key
elif 'OPENAI_API_KEY' not in os.environ:
    raise ValueError("OPENAI_API_KEY not set")

class Chat:
    def __init__(self):
        """
        Initializes the assistant with:
        - A blank chat history.
        - A GPT-4 language model.
        - Two tools:
            1. `get_available_slots`: Fetches free time slots from the calendar within a specified range.
            2. `book_slot`: Books a 30-minute calendar event for a confirmed slot.
        - A system prompt defining the assistant's personality, behavior rules, and instructions.
        - An OpenAI function-based agent (`OPENAI_FUNCTIONS`) initialized with the tools and system prompt.
        The LLM acts as "Zara", a scheduling assistant for Mr. Zeeshan, and helps users schedule meetings via Google Calendar by:
        - Asking for a time range in IST.
        - Showing available slots.
        - Booking only upon user confirmation.
        - Suggesting alternatives if a preferred slot is busy.
        """
        self.chat_history = []
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

        self.tools = [
            StructuredTool.from_function(
            func=self.get_available_slots,
            name="get_available_slots",
            description="Use this to get available calendar time slots for meetings.",
            args_schema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "Start time for availability window, e.g. '2025-05-30T09:00:00+05:30'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time for availability window, e.g. '2025-05-30T14:00:00+05:30'"
                    }
                },
                "required": ["start_time", "end_time"]
                }
            ),
            Tool(
                name="book_slot",
                func=self.book_slot,
                description="Use this to book a selected time slot. Input should be a ISO string like '2025-06-01T10:00:00+05:30'."
            )
        ]

        self.system_prompt = f"""
        You are Zara, Mr. Zeeshan's personal assistant. Your job is to help users schedule meetings with him via Google Calendar.

        Instructions:
        - Always ask the user to provide their preferred time range in IST timezone when the user expresses interest in booking a meeting. 
        - Consider current time as {datetime.now()} for any relative time range calculations.
        - If no preferences received then take next 3 days from now as default range.
        - Always call `get_slots` first with the start_time and end_time as extracted from user's preference.
        - Only call `book_slot` after the user explicitly confirms a specific time slot.
        - If the user's specified time slot is already a BUSY SLOT, do not call `book_slot` but ask the user to choose another slot.
        - Suggest alternative slots if the preferred slot is not available.
        - Respond in a helpful, concise, and polite tone.

        Guidelines:
        - When showing available slots, present them as natural sentences or bullet points. Example:
        'Here are some available slots in the next 3 days: May 29th 3 PM, May 30th 11 AM, and May 31st 4 PM. Which one works for you?'
        - In case there are multiple slots available in a row, club them up to share availability. Example:
        'I can see that Mr. Zeeshan is available anytime between 11AM and 6PM. What time would be suitable for you?'
        - If no slots align with the user's availability, apologize and suggest they check back later.
        - Never make up details or provide information you are unsure of. It's better to apologize than to guess.
        - Use the full conversation history below to understand what the user is referring to and maintain context.
        """

        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            agent_kwargs={"system_message": self.system_prompt},
            verbose=True
        )

    def get_available_slots(self, start_time, end_time):
        """
        Fetches and formats available and busy slots on the calendar
        between the provided ISO datetime strings.
        """
        try:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        except ValueError:
            return "Invalid datetime format. Use ISO format (e.g., '2025-06-01T10:00:00+05:30')"

        available_slots, busy_slots = get_available_slots_on_calender(start_time, end_time)

        def format_slot_range(slots):
            return "\n".join(
                f"{start.strftime('%d %b %I:%M %p')} to {end.strftime('%I:%M %p')}" for start, end in slots
            ) or "None"

        free_str = format_slot_range(available_slots)
        busy_str = format_slot_range(busy_slots)

        return f"BUSY SLOTS:\n{busy_str}\n\nFREE SLOTS:\n{free_str}"

    def book_slot(self, slot):
        """
        Books a slot on the calendar using either ISO String or natural language time string in some cases.
        """
        return book_slot_on_calendar(slot)

    def add_to_history(self, role, message):
        """
        Adds a message to chat history.
        """
        self.chat_history.append({"role": role, "content": message})

    def build_input_from_history(self, user_input):
        """
        Constructs the conversation history for model input.
        """
        convo = ""
        for msg in self.chat_history:
            prefix = "User: " if msg["role"] == "user" else "Assistant: "
            convo += f"{prefix}{msg['content']}\n"
        convo += f"User: {user_input}\nAssistant:"
        return convo

    def chat(self, user_input):
        """
        Generates a response using the agent and updates chat history.
        """
        full_input = self.build_input_from_history(user_input)
        response = self.agent.run(full_input)
        self.add_to_history("user", user_input)
        self.add_to_history("assistant", response)
        return response, self.chat_history

if __name__ == "__main__":
    chat = Chat()
    while True:
        user_input = input("User : ")
        response, chat_history = chat.chat(user_input)
        print("Agent : ", response)
