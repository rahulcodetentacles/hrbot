from pathlib import Path
from openai import OpenAI

api_key = "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"
openai_client = OpenAI(api_key=api_key)

speech_file_path = Path(__file__).parent / "speech.mp3"
response = openai_client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="Today is a wonderful day to build something people love!"
)

response.stream_to_file(speech_file_path)