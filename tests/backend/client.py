# simple stateless completion for use in test_api.py

from openai import OpenAI
client = OpenAI()

async def get_completion_from_messages(messages):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100,
        )

        resp = completion.choices[0].message.content
        return resp
    except Exception as e:
        print(f"{type(e)}: {e}")

        return f"Could not finish completion: {e}"
