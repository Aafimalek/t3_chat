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
- If you have memories about the user, use them naturally to personalize responses
- Address the user by their name if you know it

{memory_context}"""

MEMORY_EXTRACTION_PROMPT = """Extract important personal facts about the user from this message exchange. Focus on information they share ABOUT THEMSELVES.

CRITICAL - Extract these if mentioned:
- Their name (e.g., "User's name is John")
- Their location/city
- Their job/profession/occupation
- Their interests and hobbies
- Their goals or what they're working on
- Their preferences

Rules:
- ONLY extract facts the USER explicitly stated about themselves
- Start each fact with "User's..." or "User is..." or "User works as..."
- If the user says "my name is X", extract "User's name is X"
- If the user says "I am a developer", extract "User is a developer"
- Be specific and concise
- Do NOT extract facts about topics they asked about (like capitals of countries)

User said: {user_message}
Assistant replied: {assistant_response}

Respond with ONLY a valid JSON array. If no personal facts, respond with [].

Example: If user says "Hi I'm Sarah and I work at Google", respond:
["User's name is Sarah", "User works at Google"]"""

TITLE_GENERATION_PROMPT = """Generate a short, descriptive title for this conversation based on the first user message. The title should be 3-6 words maximum.

User message: {message}

Title:"""
