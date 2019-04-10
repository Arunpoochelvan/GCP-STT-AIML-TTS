import json
import pyaudio
import wave
import glob
import time
import playsound
import io
import os
import aiml
import winsound

from google.cloud import speech
from google.cloud import texttospeech
from google.cloud.speech import enums
from google.cloud.speech import types

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME  = "temp.wav"

BRAIN_FILE="brain.dump"
aimiKernel = aiml.Kernel()

if os.path.exists(BRAIN_FILE):
    print("Loading from brain file: " + BRAIN_FILE)
    aimiKernel.loadBrain(BRAIN_FILE)
else:
    print("Parsing aiml files")
    aimiKernel.bootstrap(learnFiles="std-startup.aiml", commands="load aiml b")
    print("Saving brain file: " + BRAIN_FILE)
    aimiKernel.saveBrain(BRAIN_FILE)

speechRecognition_client = speech.SpeechClient()

speechRecognition_config = types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,sample_rate_hertz=16000,language_code='en-US')

texttospeech_client = texttospeech.TextToSpeechClient()

texttospeech_voice = texttospeech.types.VoiceSelectionParams(language_code='en-IN',ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

texttospeech_audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

while True:
    variable  = input("Hit key to say something: ")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input = True,
                        frames_per_buffer=CHUNK)

    print("started recording")
    frames =[]
    for i in range(0, int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("stopped recording")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wavefile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wavefile.setnchannels(CHANNELS)
    wavefile.setsampwidth(audio.get_sample_size(FORMAT))
    wavefile.setframerate(SAMPLE_RATE)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()

    with io.open(WAVE_OUTPUT_FILENAME, 'rb') as audio_file:
        speechRecognition_audio = types.RecognitionAudio(content=audio_file.read())

    response = speechRecognition_client.recognize(speechRecognition_config, speechRecognition_audio)
    for result in response.results:
        print('Google Says: {}'.format(result.alternatives[0].transcript))
        what_google_said = result.alternatives[0].transcript
        aiml_response = aimiKernel.respond(what_google_said)
        print("Aiml Says:", aiml_response)
        input_text = texttospeech.types.SynthesisInput(text=aiml_response)
        google_audio_response = texttospeech_client.synthesize_speech(input_text, texttospeech_voice, texttospeech_audio_config)
        with open('what_was_said_output.wav', 'wb+') as out:
             out.write(google_audio_response.audio_content)
        winsound.PlaySound('what_was_said_output.wav', winsound.SND_FILENAME)
        os.remove("what_was_said_output.wav")
