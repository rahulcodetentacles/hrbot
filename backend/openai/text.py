from openai import OpenAI

api_key = "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"
openai_client = OpenAI(api_key=api_key)

audio_file= open("/path/to/file/audio.mp3", "rb")
transcript = openai_client.audio.transcriptions.create(
  model="whisper-1", 
  file=audio_file
)