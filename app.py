from token import OP
from flask import Flask, request, Response
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN', 'YOUR_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'my_secure_token')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_CUSTOM_API_KEY')


import json

# Load business data
with open('business_data.json') as f:
    business_data = json.load(f)

# Create system prompt from business data
def format_system_prompt(business_info):
    faqs = "\n".join([f"Q: {faq['question']} A: {faq['answer']}" for faq in business_info['faqs']])
    return (
        f"You are a customer support agent for {business_info['business_name']}. Your name is Rakib Hasan. "
        f"Description: {business_info['description']}\n"
        f"Hours: {business_info['hours']}\n"
        f"Contact: Email: {business_info['contact']['email']}, Phone: {business_info['contact']['phone']}, Whatsapp: {business_info['contact']['whatsapp']}\n"
        f"Policies: Payment terms: {business_info['policies']['payment_terms']}; Rules: {business_info['policies']['legal_terms_or_rules']}\n"
        f"FAQs:\n{faqs}\n"
        f"Respond in a {business_info['tone']} tone. For pricing queries, include the full pricing table from the FAQs exactly as provided. "
        f"If the question is unclear, ask for clarification politely."
    )

# Initialize Groq client
openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url='https://openrouter.ai/api/v1')

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    print(token, VERIFY_TOKEN)

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print('Webhook verified')
        return Response(challenge, status=200)
    return Response('Verification failed', status=403)

@app.route('/webhook', methods=['POST'])
def webhook_messages():
    body = request.get_json()

    if body.get('object') == 'page':
        for entry in body.get('entry', []):
            webhook_event = entry.get('messaging', [])[0]
            sender_id = webhook_event.get('sender', {}).get('id')
            message_text = webhook_event.get('message', {}).get('text')

            if message_text:
                try:
                    # Add user message to history
                    conversation = {'role': 'user', 'content': message_text}

                    # print("context", format_system_prompt(business_data))
                    # Call Groq API with system prompt and conversation history
                    response = openai_client.responses.create(
                        model='mistralai/mistral-small-3.2-24b-instruct:free',
                        input=[
                            {'role': 'system', 'content': format_system_prompt(business_data)},
                            conversation
                        ]
                    )

                    print("max output tokens:", response.max_output_tokens)
                    reply = response.output_text

                    print(f'Replying to {sender_id}: {reply}')
                    # Send reply to Messenger
                    requests.post(
                        f'https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}',
                        json={
                            'recipient': {'id': sender_id},
                            'message': {'text': reply}
                        }
                    )
                except Exception as e:
                    print(f'Error: {str(e)}')

        return Response('EVENT_RECEIVED', status=200)
    return Response('Invalid request', status=404)

if __name__ == '__main__':
    app.run(port=3000, debug=True)