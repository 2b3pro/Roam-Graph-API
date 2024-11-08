#!/usr/bin/env python3
"""
Multi-Prompt AI Text Processor

Version: 1.2.1
Author: AI Assistant
Date: July 9, 2024

Description:
This script processes either a single text file or multiple text files in a folder using various AI APIs
(OpenAI, Claude, or Gemini). It applies prompts from a specific file to each input file, maintaining
conversation history across files. The script supports status tracking and can handle both individual
files and folders. It also includes a function to convert PDF to text using pdftotext.

Usage:
python script_name.py /path/to/input/file_or_folder [-p prompt_file.txt] -o final_output.txt -a openai -s status.txt

Arguments:
  input_path           Path to the input file or folder containing text files
  -p, --prompt         Name of the prompt file in the PROMPTS_FOLDER directory (default: default.txt)
  -o, --output         Name of the final output file (default: final_output.txt)
  -a, --api            Choose API: openai, claude, or gemini (default: openai)
  -s, --status         Name of the status file (default: status.txt)

Requirements:
- Python 3.6+
- openai
- anthropic
- google-generativeai
- python-dotenv

Environment Variables:
- OPENAI_API_KEY: API key for OpenAI
- ANTHROPIC_API_KEY: API key for Anthropic (Claude)
- GOOGLE_API_KEY: API key for Google (Gemini)
- PROMPTS_FOLDER: Path to the folder containing prompt files
- PATH_TO_PDFTOTEXT: Path to the pdftotext executable

Note: Ensure all required API keys, PROMPTS_FOLDER, and PATH_TO_PDFTOTEXT are set in the .env file
in the same directory as the script. A 'default.txt' prompt file should be present in the PROMPTS_FOLDER.

Change Log:
- 1.2.1 (2024-07-09): Added default prompt file option
- 1.2.0 (2024-07-09): Added support for processing single files, introduced PDF to text conversion function
- 1.1.0 (2024-07-09): Added ability to choose specific prompt file and use PROMPTS_FOLDER environment variable
- 1.0.0 (2024-07-09): Initial release with support for OpenAI, Claude, and Gemini APIs,
					  multiple prompts, and conversation history.

License: MIT License

Copyright (c) 2024 AI Assistant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import argparse
import logging
import subprocess
from dotenv import load_dotenv
import openai
import anthropic
import google.generativeai as genai
from typing import List, Callable, Dict, Any

# Script version
__version__ = "1.2.1"

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_status(status_file: str, current: int, total: int):
	"""Update the status file with current progress."""
	with open(status_file, 'w') as f:
		f.write(f"{current}/{total}")

def set_final_status(status_file: str, status: str):
	"""Set the final status in the status file."""
	with open(status_file, 'w') as f:
		f.write(status)

def read_prompts(prompt_file: str) -> List[str]:
	"""Read prompts from the specified file in the PROMPTS_FOLDER."""
	prompts_folder = os.getenv('PROMPTS_FOLDER')
	if not prompts_folder:
		raise ValueError("PROMPTS_FOLDER environment variable is not set.")

	prompt_path = os.path.join(prompts_folder, prompt_file)
	if not os.path.exists(prompt_path):
		if prompt_file == "default.txt":
			raise FileNotFoundError(f"Default prompt file not found: {prompt_path}")
		logging.warning(f"Specified prompt file not found: {prompt_path}. Using default.txt")
		prompt_path = os.path.join(prompts_folder, "default.txt")
		if not os.path.exists(prompt_path):
			raise FileNotFoundError(f"Default prompt file not found: {prompt_path}")

	with open(prompt_path, 'r') as file:
		return file.read().splitlines()

def convert_pdf_to_text(pdf_path: str, output_path: str):
	"""Convert a PDF file to text using pdftotext."""
	pdftotext_path = os.getenv('PATH_TO_PDFTOTEXT')
	if not pdftotext_path:
		raise ValueError("PATH_TO_PDFTOTEXT environment variable is not set.")

	try:
		subprocess.run([pdftotext_path, pdf_path, output_path], check=True)
	except subprocess.CalledProcessError as e:
		logging.error(f"Error converting PDF to text: {str(e)}")
		raise

def process_file(file_path: str, prompts: List[str], api_function: Callable, conversation_history: List[Dict[str, str]], client: Any) -> str:
	"""Process a single file using the given API function and update conversation history."""
	with open(file_path, 'r') as file:
		content = file.read()

	results = []
	try:
		for prompt in prompts:
			result = api_function(content, prompt, conversation_history, client)
			results.append(result)
			# Update conversation history
			conversation_history.append({"role": "user", "content": content})
			conversation_history.append({"role": "assistant", "content": result})
			content = result  # Use the result as input for the next prompt
		return "\n\n".join(results)
	except Exception as e:
		logging.error(f"Error processing file {file_path}: {str(e)}")
		return ""

def openai_api_call(content: str, prompt: str, conversation_history: List[Dict[str, str]], client: Any) -> str:
	"""Make an API call to OpenAI's GPT."""
	try:
		messages = [{"role": "system", "content": prompt}] + conversation_history + [{"role": "user", "content": content}]
		response = client.ChatCompletion.create(
			model="gpt-3.5-turbo",  # Use the latest available model
			messages=messages
		)
		return response.choices[0].message.content
	except Exception as e:
		logging.error(f"OpenAI API error: {str(e)}")
		raise

def claude_api_call(content: str, prompt: str, conversation_history: List[Dict[str, str]], client: Any) -> str:
	"""Make an API call to Claude AI."""
	try:
		# Construct conversation history string
		history_str = ""
		for message in conversation_history:
			if message["role"] == "user":
				history_str += f"{anthropic.HUMAN_PROMPT} {message['content']}\n\n"
			elif message["role"] == "assistant":
				history_str += f"{anthropic.AI_PROMPT} {message['content']}\n\n"

		full_prompt = f"{anthropic.HUMAN_PROMPT} {prompt}\n\nConversation history:\n{history_str}\nNew content to process:\n{content}{anthropic.AI_PROMPT}"

		response = client.completion(
			prompt=full_prompt,
			model="claude-2.0",  # Use the latest available model
			max_tokens_to_sample=1000,
		)
		return response.completion
	except Exception as e:
		logging.error(f"Claude API error: {str(e)}")
		raise

def gemini_api_call(content: str, prompt: str, conversation_history: List[Dict[str, str]], client: Any) -> str:
	"""Make an API call to Google's Gemini AI."""
	try:
		# Construct conversation history
		chat = client.start_chat(history=[
			{"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
			for msg in conversation_history
		])

		# Add system prompt and new content
		full_prompt = f"{prompt}\n\nNew content to process:\n{content}"
		response = chat.send_message(full_prompt)

		return response.text
	except Exception as e:
		logging.error(f"Gemini API error: {str(e)}")
		raise

def process_input(input_path: str, prompts: List[str], output_file: str, api_function: Callable, status_file: str, client: Any):
	"""Process input (either a single file or a folder) using the given API function."""
	results = []
	conversation_history = []

	if os.path.isfile(input_path):
		# Process single file
		update_status(status_file, 1, 1)
		logging.info(f"Processing file: {input_path}")
		result = process_file(input_path, prompts, api_function, conversation_history, client)
		results.append(result)
	elif os.path.isdir(input_path):
		# Process folder
		tmp_folder = os.path.join(input_path, "tmp texts")
		os.makedirs(tmp_folder, exist_ok=True)

		txt_files = [f for f in os.listdir(input_path) if f.endswith('.txt')]
		total_files = len(txt_files)

		for current, filename in enumerate(txt_files, 1):
			update_status(status_file, current, total_files)
			file_path = os.path.join(input_path, filename)
			logging.info(f"Processing file: {filename}")

			result = process_file(file_path, prompts, api_function, conversation_history, client)

			# Save individual result
			tmp_output_path = os.path.join(tmp_folder, f"processed_{filename}")
			with open(tmp_output_path, 'w') as tmp_file:
				tmp_file.write(result)

			results.append(result)
	else:
		raise ValueError(f"Invalid input path: {input_path}")

	# Create final output
	final_output = "\n\n".join(results)
	output_path = os.path.join(os.path.dirname(input_path), output_file)
	with open(output_path, 'w') as final_file:
		final_file.write(final_output)

	# Save conversation history
	history_path = os.path.join(os.path.dirname(input_path), "conversation_history.txt")
	with open(history_path, 'w') as history_file:
		for message in conversation_history:
			history_file.write(f"{message['role']}: {message['content']}\n\n")

	logging.info(f"Processing complete. Final output saved to {output_path}")
	logging.info(f"Conversation history saved to {history_path}")

	set_final_status(status_file, "STATUS")

def main():
	parser = argparse.ArgumentParser(description=f"Multi-Prompt AI Text Processor v{__version__}")
	parser.add_argument("input_path", help="Path to the input file or folder containing text files")
	parser.add_argument("-p", "--prompt", default="default.txt", help="Name of the prompt file in the PROMPTS_FOLDER directory (default: default.txt)")
	parser.add_argument("-o", "--output", default="final_output.txt", help="Name of the final output file")
	parser.add_argument("-a", "--api", choices=["openai", "claude", "gemini"], default="openai", help="Choose API: openai, claude, or gemini")
	parser.add_argument("-s", "--status", default="status.txt", help="Name of the status file")
	parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
	args = parser.parse_args()

	# Read prompts from the specified file
	try:
		prompts = read_prompts(args.prompt)
	except FileNotFoundError:
		logging.error(f"Prompt file '{args.prompt}' not found and default.txt is missing. Please provide a valid prompt file.")
		return

	if not prompts:
		logging.warning("No prompts found in the specified file. Processing will continue without prompts.")

	# Set up API key and function based on chosen API
	if args.api == "openai":
		api_key = os.getenv("OPENAI_API_KEY")
		if not api_key:
			raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
		openai.api_key = api_key
		client = openai
		api_function = openai_api_call
	elif args.api == "claude":
		api_key = os.getenv("ANTHROPIC_API_KEY")
		if not api_key:
			raise ValueError("Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
		client = anthropic.Client(api_key=api_key)
		api_function = claude_api_call
	else:  # gemini
		api_key = os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise ValueError("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
		genai.configure(api_key=api_key)
		client = genai.GenerativeModel('gemini-pro')
		api_function = gemini_api_call

	status_file = os.path.join(os.path.dirname(args.input_path), args.status)
	try:
		process_input(args.input_path, prompts, args.output, api_function, status_file, client)
	except Exception as e:
		error_message = str(e)
		logging.error(f"An error occurred: {error_message}")
		set_final_status(status_file, f"ERROR|{error_message}")
		raise

if __name__ == "__main__":
	main()