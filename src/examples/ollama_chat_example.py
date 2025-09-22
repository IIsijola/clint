"""
Ollama chat example - Test local LLM with user input
"""

import ollama
import time

def main():
    print("🤖 Ollama Chat Example")
    print("=" * 50)
    print("💡 Type 'quit' or 'exit' to stop the conversation")
    print("=" * 50)
    
    while True:
        # Get user input
        user_input = input("\n💬 Enter your message: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            print("❌ Error: Message cannot be empty!")
            continue
        
        print(f"\n🔄 Processing with Ollama...")
        print(f"📝 Input: {user_input}")
        print("-" * 50)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Call Ollama API
            resp = ollama.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": user_input}],
            )
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract and display response
            response_content = resp["message"]["content"]
            print(f"🤖 Response:")
            print(response_content)
            print("-" * 50)
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            print("=" * 50)
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"❌ Error: {e}")
            print(f"⏱️  Failed after: {processing_time:.2f} seconds")

if __name__ == "__main__":
    main()
