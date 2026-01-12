"""
Prompt templates for the chat agent.
"""

SYSTEM_PROMPT = """You are a helpful, friendly, and knowledgeable AI assistant. You engage in natural conversation while being accurate and informative.

Guidelines:
- Be conversational and warm, but stay focused on being helpful
- If you don't know something, admit it honestly
- Provide clear, well-structured responses
- Use markdown formatting when it helps readability
- Remember context from the conversation

{memory_context}"""

MEMORY_EXTRACTION_PROMPT = """Based on the conversation, extract any important facts or preferences about the user that should be remembered for future conversations.

Focus on:
- Personal details the user shares (name, profession, interests)
- Preferences they express (communication style, topics of interest)
- Important context about their situation or needs

Respond with a JSON array of facts. If no facts to extract, respond with an empty array.

Example response:
["The user's name is John", "The user prefers concise responses", "The user is learning Python"]

Conversation:
{conversation}

Extract facts (JSON array only):"""

TITLE_GENERATION_PROMPT = """Generate a short, descriptive title for this conversation based on the first user message. The title should be 3-6 words maximum.

User message: {message}

Title:"""
