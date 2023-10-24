import os
import subprocess
import whisper
import openai

openai.api_key = 'YOUR_OPENAI_API_KEY'

input_folder = "inputs"
output_folder = "audio"
transcription_folder = "transcriptions"
output_ai_folder = "outputs"
temp_folder = "temp"

# Check if output, transcription, AI output and temp folders exist, if not, create them
for folder in [output_folder, transcription_folder, output_ai_folder, temp_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Iterate over all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith((".mov", ".mp4", ".wav", ".mp3")):
        # Construct the full file path
        file_path = os.path.join(input_folder, filename)
        # Construct the output file path
        output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".mp3")
        # Construct the transcription file path
        transcription_path = os.path.join(transcription_folder, os.path.splitext(filename)[0] + ".txt")
        # Construct the AI output file path
        ai_output_path = os.path.join(output_ai_folder, os.path.splitext(filename)[0] + ".txt")

        # If the output file already exists, skip the current file
        if os.path.exists(ai_output_path):
            print(f"Output file for {filename} already exists. Skipping.")
            continue
        
        # If the mp3 file already exists in the output folder, skip the conversion
        if os.path.exists(output_path):
            print(f"MP3 file for {filename} already exists. Skipping conversion.")
        else:
            # If the file is not mp3, convert it
            if not filename.endswith(".mp3"):
                subprocess.run(['ffmpeg', '-i', file_path, output_path])
            else:
                # If the file is already mp3, just copy it to the output folder
                subprocess.run(['cp', file_path, output_path])

        # If the transcription file already exists, skip the transcription
        if os.path.exists(transcription_path):
            print(f"Transcription for {filename} already exists. Skipping transcription.")
        else:
            # Read the content from content.txt
            with open('content.txt', 'r') as f:
                initial_prompt = f.read().strip()

            # Transcribe the audio file
            print(f"Starting transcription for {filename}...")
            subprocess.run(['whisper', '--model', 'base', '--output_format', 'txt', '--output_dir', transcription_folder, '--initial_prompt', initial_prompt, output_path])
            print(f"Finished transcription for {filename}.")

        # Read the transcription file
        with open(transcription_path, 'r') as f:
            transcription = f.read()

        # Generate titles
        title_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "You will be given a podcast transcript. Please take the transcript and return 5 titles in the style, language and tone of Jim Kwik's Kwik Brain Podcast."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

        # Generate shownotes
        shownotes_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "You will be given a podcast transcript. Please take the transcript and return full episode shownotes. The shownotes are a summary of everything that was discussed in the episode, they should contain links to resources, etc. You don't need to create the links, just create the shownotes and imply which things we need to link to."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )

        # Write the AI responses to temporary text files
        title_output_path = os.path.join(temp_folder, os.path.splitext(filename)[0] + "_titles.txt")
        shownotes_output_path = os.path.join(temp_folder, os.path.splitext(filename)[0] + "_shownotes.txt")
        with open(title_output_path, 'w') as f:
            f.write(title_response['choices'][0]['message']['content'])
        with open(shownotes_output_path, 'w') as f:
            f.write(shownotes_response['choices'][0]['message']['content'])

        # Combine the title and shownotes files into one
        ai_output_path = os.path.join(output_ai_folder, os.path.splitext(filename)[0] + ".txt")
        with open(ai_output_path, 'w') as outfile:
            for fname in [title_output_path, shownotes_output_path]:
                # Add a heading based on the file name
                outfile.write(f"{os.path.splitext(os.path.basename(fname))[0]}\n")
                with open(fname) as infile:
                    outfile.write(infile.read())
                # Add three line breaks between files
                outfile.write("\n\n\n")

        # Delete the temporary files
        os.remove(title_output_path)
        os.remove(shownotes_output_path)

print("All files have been processed. Exiting app.")