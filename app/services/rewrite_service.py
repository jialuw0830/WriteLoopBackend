from app.services.llm_client import client
import json

def rewrite_sentence(sentence: str) -> str:
    """
    Rewrite a sentence using OpenAI API to improve English expression.
    """
    prompt = f"Rewrite this sentence in better English: {sentence}"

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]

    try:
        completion = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        rewritten_text = completion.choices[0].message.content.strip()

        response = {
            "original": sentence,
            "rewritten": rewritten_text
        }

        return json.dumps(response)

    except Exception as e:
        print(f"Error generating rewritten sentence: {e}")
        return json.dumps({"error": str(e)})
