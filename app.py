from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS  # Import CORS
from openai import OpenAI
from pathlib import Path    
import logging
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

thread = openai_client.beta.threads.create()

# Initialize interview questions and audio file paths as empty lists
questions_list = []
audio_paths = []

# Number of questions to generate
num_questions_to_generate = 5

current_question_index = 0
candidate_responses = []

def wait_for_run_completion(client, thread_id, run_id, sleep_interval=1):
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

def generate_interview_questions(prompt):
    global questions_list, audio_paths
    # Clear existing questions and file paths
    questions_list = []
    audio_paths = []

    # Generate new questions using OpenAI
    for i in range(num_questions_to_generate):
        message = f"Ask one liner questions to the candidate."
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Please address the user as a candidate giving an interview"
        )
        wait_for_run_completion(openai_client, thread.id, run.id)
        messages = openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )

        last_message = messages.data[0]
        response = last_message.content[0].text.value

        if response:
            question_str = response.strip()
            questions_list.append(question_str)

            # Save audio for each question
            response_audio = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=question_str
            )

            speech_file_path = Path(__file__).parent / f"static/question_{i}.mp3"
            response_audio.stream_to_file(speech_file_path)
            audio_paths.append(str(speech_file_path))

@app.route("/")
def interview_form():
    return render_template("interview_form.html")

@app.route("/interview")
def interview():
    return render_template("interview.html")


@app.route("/submit_form", methods=["POST"])
def submit_form():
    global prompt, assistant
    # Get form data
    years_of_experience = request.form.get("years_of_experience")
    position = request.form.get("position")
    # Add more fields as needed

    # Generate interview questions based on the form data
    prompt = f"The interview questions are for a candidate with {years_of_experience} years of experience applying for a {position} position"

    # Update the assistant instructions with the new prompt
    assistant = openai_client.beta.assistants.create(
        name="HR Interviewer",
        instructions=f"You are an experienced HR interviewer conducting a job interview for a technical position. Begin the interview with casual and friendly conversation to make the candidate comfortable. Ask about their day, interests, or any recent achievements. Then, transition into more specific technical questions. Dive into the candidate's past projects, problem-solving abilities, and teamwork skills. Inquire about specific examples and seek details on how they handled challenges. Assess their communication and interpersonal skills. Provide a friendly and professional environment, allowing the candidate to showcase their strengths. Tailor your questions based on the candidate's responses to gather a comprehensive understanding. Keep the conversation engaging, and feel free to adapt your approach based on the candidate's background and responses.{prompt}",
        model="gpt-4",
    )

    # Redirect to the index page
    return redirect(url_for('interview'))

@app.route("/get_question")
def get_question():
    global current_question_index, questions_list
    print(f"Current Index: {current_question_index}, Num Questions: {num_questions_to_generate}")
    if current_question_index < len(questions_list):
        current_question = questions_list[current_question_index]
        current_question_index += 1
        print(f"Returning Question: {current_question}")
        return jsonify({"question": current_question, "questionIndex": current_question_index - 1})
    elif current_question_index < num_questions_to_generate:
        # If not all questions have been generated, generate new ones
        generate_interview_questions(prompt)
        current_question_index = 0
        return jsonify({"question": questions_list[current_question_index], "questionIndex": current_question_index})
    else:
        # All questions have been answered
        print("All Questions Answered. Returning None.")
        return jsonify({"question": None, "questionIndex": None})


@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    global candidate_responses, current_question_index
    audio_file = request.files.get("answer")

    candidate_responses.append(audio_file)

    # Check if there are more questions, if yes, increment the index
    if current_question_index < num_questions_to_generate - 1:
        current_question_index += 1

    return jsonify({"status": "success"})

@app.route("/get_assessment")
def get_assessment():
    questions_and_answers = []

    # Combine questions and answers
    for i, question in enumerate(questions_list):
        questions_and_answers.append(f"Q: {question}")
        if i < len(candidate_responses):
            questions_and_answers.append(f"A: {candidate_responses[i]}")

    assessment_input = "\n".join(questions_and_answers)

    # Send combined questions and answers to OpenAI with additional instruction
    assessment_prompt = (
        "You are an HR interviewer. Please analyze the candidate's interview performance. "
        "Provide an interview score out of 10 and a verdict on whether the candidate should be selected for further rounds. "
        "Additionally, add a one sentence super short comment on the interview performance. The assessment must be strict."
    )

    # Combine the prompt and user input
    conversation_history = f"{assessment_prompt}\n\n{assessment_input}"

    # Send the conversation history to OpenAI
    assessment = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an HR interviewer."},
            {"role": "assistant", "content": assessment_prompt},
            {"role": "user", "content": conversation_history},
        ],
    ).choices[0].message.content

    return jsonify({"assessment": assessment})

if __name__ == "__main__":
    app.run(debug=True)
