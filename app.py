from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Import CORS
from openai import OpenAI
from pathlib import Path    

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# OpenAI API key
api_key = "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"
openai_client = OpenAI(api_key=api_key)

# Initialize interview questions and audio file paths as empty lists
questions_list = []
audio_paths = []

# Number of questions to generate
num_questions_to_generate = 2

current_question_index = 0
candidate_responses = []

def generate_interview_questions():
    global questions_list, audio_paths
    # Clear existing questions and file paths
    questions_list = []
    audio_paths = []

    # Generate new questions using OpenAI
    for i in range(num_questions_to_generate):
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "assistant", "content": "Generate an interview question related to solidity"},
            ],
        )

        if response.choices:
            question_str = response.choices[0].message.content.strip()
            questions_list.append(question_str)

            if i == 0:  # Save audio only for the first question
                response_audio = openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=question_str
                )

                speech_file_path = Path(__file__).parent / "static/question.mp3"
                response_audio.stream_to_file(speech_file_path)
                audio_paths.append(str(speech_file_path))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_question")
def get_question():
    global current_question_index, questions_list
    if current_question_index < len(questions_list):
        current_question = questions_list[current_question_index]
        current_question_index += 1
        return jsonify({"question": current_question})
    elif not questions_list:
        # If no questions exist, generate new ones
        generate_interview_questions()  
        current_question_index = 0
        return jsonify({"question": questions_list[current_question_index]})
    else:
        # All questions have been answered
        return jsonify({"question": None})

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    global candidate_responses, current_question_index
    audio_file = request.files.get("answer")
    
   
    candidate_responses.append(audio_file)
    
    # Check if there are more questions, if yes, increment the index
    if current_question_index < len(questions_list):
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

    # Send combined questions and answers to OpenAI
    assessment = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an HR interviewer."},
            {"role": "assistant", "content": "Please analyze the candidate's interview performance."},
            {"role": "user", "content": assessment_input},
        ],
    ).choices[0].message.content

    return jsonify({"assessment": assessment})

if __name__ == "__main__":
    app.run(debug=True)
