import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Use Groq with a fast free model
llm = ChatGroq(
    api_key=GROQ_API_KEY, 
    model="llama-3.3-70b-versatile",  # Fast and free
    temperature=0.5
)

class WaterIntakeAgent():
    
    def __init__(self):
        self.history = []
        
    def analyze_intake(self, intake_ml):
        
        prompt = f"""
        You are a hydration assistant. The user has consumed {intake_ml} ml of water today.
        Provide a hydration status and suggest if they need to drink more water.
        Be concise and helpful (2-3 sentences).
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return response.content

if __name__ == "__main__":
    agent = WaterIntakeAgent()
    intake_ml = 1500 
    feedback = agent.analyze_intake(intake_ml)
    print(f"Hydration analysis: {feedback}")