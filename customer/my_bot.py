import asyncio
import os
import random
import shutil
import re
import subprocess
import requests
import sqlite3
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from groq import InternalServerError
from langchain.chains import LLMChain
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

load_dotenv()

# List of audio files
audio_files = [
    'wait.mp3',
    'patiant.mp3',
    'checking.mp3',
    'getting.mp3',
    'hold.mp3',
    'find.mp3'
]

class LanguageModelProcessor:
    def __init__(self, db_path="Restaurant.db"):
        self.llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768", groq_api_key=os.getenv("GROQ_API_KEY"))
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.db_path = db_path
        self.state = "check_intent"  # Default state for checking user's intent
        self.requested_time = None  # Placeholder for user-specified reservation time
        self.required_seats = 1  # Default required seats, will be updated based on user input
        
        with open('system_prompt.txt', 'r') as file:
            system_prompt = file.read().strip()
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])

        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )
    
    def process(self, text):
        start_time = time.time()
        self.memory.chat_memory.add_user_message(text)

        try:
            if "people" in text.lower():
                self.required_seats = int(re.search(r'\b(\d+)\b', text).group(1))

            if "reserve" in text.lower():
                self.requested_time = self.extract_time_from_text(text)
                if self.requested_time:
                    response_text = self.handle_reservation_request(self.requested_time)
                else:
                    response_text = "Please specify a time for the reservation."

            else:
                response = self.conversation.invoke({"text": text})
                response_text = response['text']

        except InternalServerError as e:
            response_text = "I'm having trouble connecting to my language model service. Please try again shortly."

        end_time = time.time()
        self.memory.chat_memory.add_ai_message(response_text)
        elapsed_time = int((end_time - start_time) * 1000)
        print(f"LLM ({elapsed_time}ms): {response_text}")
        return response_text

    def extract_time_from_text(self, text):
        match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)\b', text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)  # Default to 0 if minutes are not provided
            period = match.group(3).upper()
            
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0

            now = datetime.now()
            reservation_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if reservation_time < now:
                reservation_time += timedelta(days=1)

            return reservation_time
        return None

    def handle_reservation_request(self, requested_time):
        duration_hours = 1.5
        requested_end_time = requested_time + timedelta(hours=duration_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check tables with enough seats, considering tables with a past `occupied_end_time`
            cursor.execute("""
                SELECT table_id, table_number, seats 
                FROM "Table"
                WHERE seats >= ? 
                AND (status = 'Available' OR (occupied_end_time IS NOT NULL AND occupied_end_time <= ?))
                ORDER BY seats ASC, occupied_end_time ASC
            """, (self.required_seats, requested_time))
            
            rows = cursor.fetchall()

            if rows:
                table_id, table_number, seats = rows[0]
                self.reserve_table(table_id, requested_time, requested_end_time)
                return f"Table {table_number} with {seats} seats has been reserved from {requested_time.strftime('%I:%M %p')} to {requested_end_time.strftime('%I:%M %p')}."
            
            # If no exact match, suggest alternative tables
            cursor.execute("""
                SELECT table_number, seats, occupied_end_time
                FROM "Table"
                WHERE status = 'Available' OR occupied_end_time IS NOT NULL
                ORDER BY occupied_end_time ASC
                LIMIT 3
            """)
            
            alternative_times = cursor.fetchall()
            suggestions = []
            for table_number, seats, occupied_end_time in alternative_times:
                if occupied_end_time:  # Only parse if it's not None
                    try:
                        occupied_end_time = datetime.strptime(occupied_end_time, '%Y-%m-%d %H:%M:%S')
                        suggestions.append(
                            f"Table {table_number} with {seats} seats available after {occupied_end_time.strftime('%I:%M %p')}"
                        )
                    except ValueError:
                        suggestions.append(
                            f"Table {table_number} with {seats} seats available (end time not properly formatted)"
                        )
                else:
                    suggestions.append(
                        f"Table {table_number} with {seats} seats available (end time not available)"
                    )
                    
            return "Unfortunately, no tables are available at that time. Here are some alternatives:\n" + "\n".join(suggestions)

    def reserve_table(self, table_id, start_time, end_time):
        # Reserve the specified table in the database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE "Table"
                SET status = 'Reserved', occupied_start_time = ?, occupied_end_time = ?
                WHERE table_id = ?
            """, (start_time, end_time, table_id))
            conn.commit()



class TextToSpeech:
    DG_API_KEY = os.getenv("DEEPGRAM_API_KEY")

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        lib = shutil.which(lib_name)
        return lib is not None

    def speak(self, text):
        if not self.is_installed("ffplay"):
            raise ValueError("ffplay not found, necessary to stream audio.")

        DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?encoding=linear16&sample_rate=24000"
        headers = {
            "Authorization": f"Token {self.DG_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }

        player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
        player_process = subprocess.Popen(
            player_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    player_process.stdin.write(chunk)
                    player_process.stdin.flush()

        if player_process.stdin:
            player_process.stdin.close()
        player_process.wait()


class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)

transcript_collector = TranscriptCollector()

async def get_transcript(callback, audio_segment):
    transcription_complete = asyncio.Event()

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram: DeepgramClient = DeepgramClient("", config)

        dg_connection = deepgram.listen.asynclive.v("1")
        print("Listening...")

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            
            if not result.speech_final:
                transcript_collector.add_part(sentence)
            else:
                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                if len(full_sentence.strip()) > 0:
                    full_sentence = full_sentence.strip()
                    print(f"Human: {full_sentence}")
                    callback(full_sentence)
                    transcript_collector.reset()
                    transcription_complete.set()

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-2-phonecall",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300,
            smart_format=True,
        )

        await dg_connection.start(options)

        microphone = Microphone(dg_connection.send)
        microphone.start()

        await transcription_complete.wait()

        microphone.finish()
        await dg_connection.finish()

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

class ConversationManager:
    def __init__(self):
        self.transcription_response = ""
        self.llm = LanguageModelProcessor()
        self.audio_segment = None

    async def main(self):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence

        while True:
            selected_audio = random.choice(audio_files)
            self.audio_segment = AudioSegment.from_file(selected_audio)

            await get_transcript(handle_full_sentence, self.audio_segment)
            
            if "goodbye" in self.transcription_response.lower():
                break

            llm_response = self.llm.process(self.transcription_response)
            
            tts = TextToSpeech()
            play(self.audio_segment)
            tts.speak(llm_response)

            self.transcription_response = ""

if __name__ == "__main__":
    manager = ConversationManager()
    asyncio.run(manager.main())

