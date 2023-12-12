from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from openai import OpenAI
from pathlib import Path
import logging
import time
import base64
import io
import speech_recognition as sr

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

thread = openai_client.beta.threads.create()
print("Thread ID: ", thread.id)

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
    questions_list = []
    audio_paths = []

    for i in range(num_questions_to_generate):
        if i == 0:
            message = f"Ask a casual question, which can include a friendly greeting or any question that helps establish a positive and comfortable atmosphere for the conversation. Keep it super simple."
        elif i == 1:
            message = f"Ask a question that encourages the candidate to share a bit about their experiences or interests outside of work, contributing to a more relaxed and personable exchange. Keep it super simple."
        elif i == 2:
            message = f"Inquire about the candidate's professional journey. Pose a question that invites them to share a memorable or impactful experience from their career, fostering a positive and open dialogue. Keep it super simple."
        elif i == 3:
            message = f"Ask a simple yet insightful question about a specific accomplishment or project you've worked on in your previous roles. This will help us understand how your background aligns with the requirements of the position. Keep it super simple."
        else:
            message = f"Ask a simple question. {prompt}"

        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_vtxuvk3SFm97GvMqgZWxGpUd",
            instructions="This is a HR interview"
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

            response_audio = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=question_str
            )

            speech_file_path = Path(__file__).parent / f"static/question_{i}.mp3"
            response_audio.stream_to_file(speech_file_path)
            audio_paths.append(str(speech_file_path))

@app.route("/submit_form", methods=["POST"])
def submit_form():
    global prompt, assistant
    years_of_experience = request.form.get("years_of_experience")
    position = request.form.get("position")

    prompt = f"The interview questions are for a candidate with {years_of_experience} years of experience applying for a {position} position"

    # assistant = openai_client.beta.assistants.create(
    #     name="HR Interviewer",
    #     instructions=f"You are an experienced HR interviewer conducting a job interview for a technical position. Begin the interview with casual and friendly conversation to make the candidate comfortable. Ask about their day, interests, or any recent achievements. Then, transition into more specific technical questions. Dive into the candidate's past projects, problem-solving abilities, and teamwork skills. Inquire about specific examples and seek details on how they handled challenges. Assess their communication and interpersonal skills. Provide a friendly and professional environment, allowing the candidate to showcase their strengths. Tailor your questions based on the candidate's responses to gather a comprehensive understanding. Keep the conversation engaging, and feel free to adapt your approach based on the candidate's background and responses.{prompt}",
    #     model="gpt-3.5-turbo",
    # )

    return jsonify({"status": "success", "message": "Form submitted successfully"})

@app.route("/get_question", methods=["GET"])
def get_question():
    global current_question_index, questions_list
    print(f"Current Index: {current_question_index}, Num Questions: {num_questions_to_generate}")
    if current_question_index < len(questions_list):
        current_question = questions_list[current_question_index]
        current_question_index += 1  # Increment here for the next question
        return jsonify({"question": current_question, "questionIndex": current_question_index - 1})
    elif current_question_index < num_questions_to_generate:
        generate_interview_questions(prompt)
        current_question_index = 0  # Reset the index for the new set of questions
        return jsonify({"question": questions_list[current_question_index], "questionIndex": current_question_index})
    else:
        print("All Questions Answered. Returning None.")
        return jsonify({"question": None, "questionIndex": None})

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    global candidate_responses, current_question_index
    audio_file = request.form.get("answer")
    print("This is audio file" ,audio_file)

    candidate_responses.append(audio_file)
    print("This is candidate responses", candidate_responses)

    return jsonify({"status": "success"})

@app.route("/get_assessment")
def get_assessment():
    questions_and_answers = []

    for i, question in enumerate(questions_list):
        questions_and_answers.append(f"Q: {question}")
        if i < len(candidate_responses):
            questions_and_answers.append(f"A: {candidate_responses[i]}")

    assessment_input = "\n".join(questions_and_answers)

    assessment_prompt = (
        "You are an HR interviewer. Please analyze the candidate's interview performance. "
        "Provide an interview score out of 10 and a verdict on whether the candidate should be selected for further rounds. "
        "Additionally, add a one sentence super short comment on the interview performance. The assessment must be strict."
        "Keep it super simple."
    )

    conversation_history = f"{assessment_prompt}\n\n{assessment_input}"

    assessment = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an HR interviewer."},
            {"role": "assistant", "content": assessment_prompt},
            {"role": "user", "content": conversation_history},
        ],
    ).choices[0].message.content

    return jsonify({"assessment": assessment})

def handle_audio_data(data):
    global current_question_index, candidate_responses

    audio_data = data['audio_data']
    audio_data_bytes = base64.b64decode(audio_data)

    # Convert audio to text using Speech Recognition API
    text = convert_audio_to_text(audio_data_bytes)

    candidate_responses.append(text)
    print("This is candidate responses", candidate_responses)

    if current_question_index < num_questions_to_generate - 1:
        current_question_index += 1

    emit('question_request', {'index': current_question_index})

def convert_audio_to_text(audio_data_bytes):
    recognizer = sr.Recognizer()
    audio_data = io.BytesIO(audio_data_bytes)

    try:
        with sr.AudioFile(audio_data) as source:
            audio_text = recognizer.recognize_google(
                source, show_all=False
            )
            print("Transcription:", audio_text)
            return audio_text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

if __name__ == "__main__":
    socketio.run(app, debug=True)
