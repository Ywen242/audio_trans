import tkinter as tk
from tkinter import ttk
import threading
import requests
import json
import time
import os
from pydub import AudioSegment
import tempfile

class AudioProcessor:
    # This class contains methods for processing audio files.
    def __init__(self, api_token, base_url, local_path):
        # Initialize the AudioProcessor with API token, base URL, and local file path.
        self.api_token = api_token
        self.base_url = base_url
        self.local_path = local_path
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }

    def transcript_audio(self, file_name):
        # Transcribe audio using AssemblyAI's API.
        # This method sends a request to the transcription service and polls for the result.
        # This part of code can be find from the instructions of AssemblyAI's API.
        transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
        data = {"audio_url": self.base_url + file_name + ".mp3", "speaker_labels": True}
        response = requests.post(transcript_endpoint, json=data, headers=self.headers)
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{response.json()['id']}"

        while True:
            result = requests.get(polling_endpoint, headers=self.headers).json()
            if result['status'] == 'completed':
                return result
            elif result['status'] == 'error':
                raise RuntimeError(f"Transcription failed: {result['error']}")
            time.sleep(3)

    def clip_time(self, transcription_result):
        # Process transcription results to identify segments based on selected speakers.
        merged_result, segments = [], []
        current_speaker, current_start, current_end = None, None, None

        # Merge transcription by speakers.
        for word in transcription_result['words']:
            if word['speaker'] == current_speaker:
                current_end = word['end']
            else:
                if current_speaker is not None:
                    merged_result.append({'speaker': current_speaker, 'start': current_start, 'end': current_end})
                current_speaker, current_start, current_end = word['speaker'], word['start'], word['end']
        merged_result.append({'speaker': current_speaker, 'start': current_start, 'end': current_end})

        filtered_result = self._filter_segments(merged_result)
        segments = [entry for entry in filtered_result if entry['end'] - entry['start'] > 3000]
        return segments

    def _filter_segments(self, merged_result):
        # Filter and process segments based on duration.
        # This method is used to identify the presenter's speaking segments in a Q&A session.
        filtered_result = []
        for speaker in set(entry['speaker'] for entry in merged_result):
            entries = [entry for entry in merged_result if entry['speaker'] == speaker]
            filtered_entries = [entry for entry in entries if entry['end'] - entry['start'] < 90000] # Clips longer than 90s are considered presentation sessions.
            if any(entry['end'] - entry['start'] > 90000 for entry in entries): # Speakers with presentation sessions are considered presenters.
                filtered_result.extend(filtered_entries) # Retrieve clips of the presenter speaking in the Q&A session.
        return filtered_result

    def download_and_split_audio(self, file_name, segments):
        # Download and split the audio into segments based on the filtered results.
        folder_path = os.path.join(self.local_path, file_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        audio_url = self.base_url + file_name + ".mp3"

        # Use a temporary directory for processing.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_mp3_path = os.path.join(temp_dir, f'{file_name}.mp3')
            audio_data = requests.get(audio_url).content
            with open(temp_mp3_path, 'wb') as file:
                file.write(audio_data)

            audio = AudioSegment.from_mp3(temp_mp3_path)

        # Clip the audio and save the segments.
        # Rename clipped audio using the format 'Speaker_<index>_<count>.mp3'.
        speaker_order, speaker_counts = {}, {}
        for segment in segments:
            speaker = segment['speaker']
            if speaker not in speaker_order:
                speaker_order[speaker] = chr(65 + len(speaker_order))
            speaker_label = speaker_order[speaker]
            start, end = segment['start'], segment['end']
            speaker_counts[speaker_label] = speaker_counts.get(speaker_label, 0) + 1
            clip = audio[start:end]
            clip_name = f'Speaker_{speaker_label}_{speaker_counts[speaker_label]}.mp3'
            clip.export(os.path.join(folder_path, clip_name), format="mp3")

    def process_files(self, file_names, update_progress, stop_event):
        # Main method to process multiple files.
        # Updates progress and can be stopped with a stop event.
        # This method is useful for integrating with a GUI.
        for index, file_id in enumerate(file_names):
            if stop_event.is_set():
                break
            update_progress(index + 1, len(file_names), f"Processing: {file_id}")
            folder_path = os.path.join(self.local_path, file_id)
            if not os.path.exists(folder_path):
                transcription = self.transcript_audio(file_id)
                segments = self.clip_time(transcription)
                self.download_and_split_audio(file_id, segments)
        update_progress(len(file_names), len(file_names), "Completed")


class Application(tk.Tk):
    def __init__(self, processor, file_names):
        # Initialize the main application window.
        # Set up UI components including progress bar and status label.
        super().__init__()
        self.processor = processor
        self.file_names = file_names
        self.stop_event = threading.Event()

        self.title("Audio Processing")
        self.geometry("300x150")

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=280, mode='determinate')
        self.progress.pack(pady=20)

        self.status_label = tk.Label(self, text="Starting...")
        self.status_label.pack()

        self.stop_button = tk.Button(self, text="Stop", command=self.stop)
        self.stop_button.pack(pady=10)

        self.thread = threading.Thread(target=self.processor.process_files, args=(file_names, self.update_progress, self.stop_event))
        self.thread.start()

    def update_progress(self, current, total, status):
        # Information update.
        self.progress['value'] = (current / total) * 100
        self.status_label.config(text=status)
        self.update_idletasks()

    def stop(self):
        # Stop event.
        self.stop_event.set()
        self.status_label.config(text="Stopping...")
        self.stop_button.config(state=tk.DISABLED)

# Usage
api_token = "94f71f857a5549f5b1d53c316f9c31e7"
base_url = "https://github.com/Ywen242/audio_trans/raw/master/audio/"
local_path = "E:\\test_audio\\cliped_audio\\"

processor = AudioProcessor(api_token, base_url, local_path)

name_url = "https://github.com/Ywen242/audio_trans/raw/master/file_names.txt"
name_r = requests.get(name_url)

if name_r.status_code == 200:
    file_names = eval(name_r.text) # This is a file contains the names of audios need to be proceeded.
else:
    file_names = []

app = Application(processor, file_names)
app.mainloop()