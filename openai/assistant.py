from openai import OpenAI
import os
import time
import logging
from datetime import datetime

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

assistant = openai_client.beta.assistants.create(
    name="Research Assistant",
    instructions="You are a helpful research assistant. Your role is to assist in navigating and understanding research papers from ArXiv. Summarize papers, clarify terminology within context, and extract key figures and data. Cross-reference information for additional insights and answer related questions comprehensively. Analyze the papers, noting strengths and limitations. Respond to queries effectively, incorporating feedback to enhance your accuracy. Handle data securely and update your knowledge base with the latest research. Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations. Maintain a feedback loop for continuous improvement and user support. Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.",
    model="gpt-4",

)

thread = openai_client.beta.threads.create()

message = "Who are you and what do you do?"

message = openai_client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=message
)

run = openai_client.beta.threads.runs.create(
    thread_id = thread.id,
    assistant_id = assistant.id,
    instructions = "Please address the user as Gunnar. The user has a premium account."
)

def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
                logging.info(f"Run completed in {formatted_elapsed_time}")
                break
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)

wait_for_run_completion(openai_client, thread.id, run.id)

messages = openai_client.beta.threads.messages.list(
    thread_id=thread.id
    )

last_message = messages.data[0]
response = last_message.content[0].text.value
print(response)