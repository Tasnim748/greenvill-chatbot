from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_CUSTOM_API_KEY')

# Initialize Groq client
openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url='https://openrouter.ai/api/v1')


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

conversation = {'role': 'user', 'content': "Hi anyone out there ?"}

# print("context", format_system_prompt(business_data))
# Call Groq API with system prompt and conversation history
response = openai_client.chat.completions.create(
                model='mistralai/mistral-small-3.2-24b-instruct:free',
                messages=[
                    {'role': 'system', 'content': format_system_prompt(business_data)},
                    conversation
                ]
            )

print(response)