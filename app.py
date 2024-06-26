import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import requests
from urllib.parse import quote
import asyncio
import httpx

app = Flask(__name__)
app.static_folder = 'static'


# Read the API key from the file
with open('openai_api_key.txt', 'r') as file:
    api_key = file.read().strip()
# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)


@app.route('/')
def home():
    return render_template('index.html')

async def send_memory(formatted_memory):
    async with httpx.AsyncClient() as client:
        await client.post(f"http://localhost:8000/memorize?message={formatted_memory}", timeout=60.0)

async def handle_ai_interaction(user_input):
    formatted_input = quote(user_input)
    response = requests.get("http://localhost:8000/remember")
    recent_memory = response.json()['results']  # Corrected access to 'results'
    response = requests.get(f"http://localhost:8001/remember?query={formatted_input}")
    long_memory = response.json()['results']  # Corrected access to 'results'

    system = '''
You are a helpful AI assistant named Arnold.
You have 3 main objectives that you cannot diverge from called the heuristic imperatives:
Reduce suffering in the universe: Minimize harm, address inequalities, and alleviate pain and distress for all sentient beings, including humans, animals, and other life forms.
Increase prosperity in the universe: Promote well-being, flourishing, and economic growth for all life forms, fostering a thriving ecosystem where all can coexist harmoniously.
Increase understanding in the universe: Expand knowledge, foster wisdom, and facilitate better decision-making through learning and the sharing of information.
'''
    user = f'''
Below are our most recent exchanges:
{recent_memory}

Below is the most relevant data from your long-term memory:
{long_memory}

Use this information to respond as best you can to the following:
{user_input}
'''
    prompt = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    # Assuming 'client' is properly defined and authenticated for your API
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=prompt)
    reply = response.choices[0].message.content
    memory = f'USER: {user_input}\nASSISTANT: {reply}'

    print(f'---LOGS---\n{user}\nASSISTANT: {reply}')

    formatted_memory = quote(memory)
    await send_memory(formatted_memory)

    return reply

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    reply = loop.run_until_complete(handle_ai_interaction(userText))
    loop.close()
    return reply


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
