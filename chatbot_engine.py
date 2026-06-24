from datetime import datetime
import os
from groq import Groq

# ================== CONFIG ==================


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(
    api_key=GROQ_API_KEY
)



# ================== LLM FUNCTION ==================
def ask_llm(user_query):
    """Call Groq LLM safely"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent assistant. "
                        "Give clear, concise, and helpful answers. "
                        "If traffic-related, give practical insights."
                    )
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"


# ================== MAIN FUNCTION ==================
def generate_chatbot_response(user_query, traffic_df, user_role="user"):
    query_lower = user_query.lower().strip()

    # ===== SIMPLE FALLBACK (if not Bangalore traffic) =====
    if not any(word in query_lower for word in ["bangalore", "traffic", "road", "flyover", "underpass"]):
        return {
            "content": ask_llm(user_query),
            "suggestions": []
        }

    # ===== BASIC TRAFFIC RESPONSE =====
    current_time = datetime.now().strftime("%I:%M %p")
    avg_congestion = traffic_df['Congestion Level'].mean()
    avg_speed = traffic_df['Average Speed'].mean()

    response = (
        f"**Bangalore Traffic Summary**\n\n"
        f"Time: {current_time}\n"
        f"Average Congestion: {avg_congestion:.1f}%\n"
        f"Average Speed: {avg_speed:.1f} km/h\n\n"
        f"Ask about specific areas like Koramangala, Whitefield, Hebbal for detailed insights."
    )

    suggestions = [
        "Traffic in Whitefield?",
        "Why is Silk Board congested?",
        "Best time to travel?",
        "Flyover or underpass suggestion?"
    ]

    return {
        "content": response,
        "suggestions": suggestions
    }