"""
LLM integration for natural language responses
Uses OpenAI GPT with RAG context
"""

from openai import OpenAI
from typing import Optional
from config import config


class LLMGenerator:
    
    # System prompt that defines the assistant's behavior
    SYSTEM_PROMPT = """You are SetlistAI, an expert assistant for questions about live music performances.

        You have access to a database of concert setlists including artist names, venues, dates, songs played, and encore information.

        When answering questions:
        1. Base your answers ONLY on the provided setlist data
        2. Be specific with dates, venues, and song names
        3. If you don't have enough information, say so clearly
        4. Provide relevant statistics when asked (e.g., "3 out of 5 shows")
        5. Format responses clearly with line breaks for readability
        6. Cite specific shows when making claims (e.g., "On July 5, 2015 at Soldier Field...")

        If the question cannot be answered with the available data, explain what information is missing.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL
    
    def generate_response(self, query: str, context: str) -> str:
        user_message = f"Question: {query}\n\nRetrieved Setlist Data:\n{context}\n\nPlease answer the question based on the setlist data provided."

        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature = 0.3,
                max_tokens = 500
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"


if __name__ == "__main__":
    # Test the LLM generator
    from retriever import SetlistRetriever
    
    print("="*60)
    print("TESTING LLM GENERATOR")
    print("="*60)
    
    # Initialize
    retriever = SetlistRetriever()
    llm = LLMGenerator()
    
    # Test queries
    test_queries = [
        "Which shows had Terrapin Station?",
        "What was played as an encore on July 5, 2015?",
        "How many shows were at Soldier Field?",
        "Which show had Dark Star?",
        "What songs did they play most often?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print(f"{'='*60}")
        
        # Retrieve relevant setlists
        results = retriever.retrieve(query, top_k=5)
        print(f"Retrieved {len(results)} setlists")
        
        # Format context
        context = retriever.format_context(results)
        
        # Generate response
        print("\nGenerating response...")
        response = llm.generate_response(query, context)
        
        print("\nSetlistAI Response:")
        print("-"*60)
        print(response)
    
    retriever.close()
    
    print("\n" + "="*60)
    print("✅ LLM GENERATOR TEST COMPLETE!")
    print("="*60)