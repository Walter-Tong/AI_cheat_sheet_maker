#### TODO

You are going to make a AI agent for help making cheat sheet for university courses, all cheat sheets are allow to bring in to the exam.

You will need to create an agent that with the following capabilities:
1. Open all lecture notes under the `{course}/lecture_notes/` directory, to get course contents, and extract the content in lecture notes in markdown, and check if the cheatsheet have covered all important topics in the lecture notes.
2. Open and convert all files in pdf in `{course}/past_papers/` or `{course}/assignment/question` directory to text files, to check if a cheatsheet have covered all past exam questions, majorly, you need to check do the cheatsheet have provided enough information for answering the questions in past papers.

You should make use of Python

1. main.py: The main script to run the agent, this program should take an arg of course_code to specify which course to process and open the corresponding directories, for explain if the user input CS231, the folder should handle all files under `CS231/lecture_notes/`, `CS231/past_papers/` and `CS231/assignment/question/`
2. file_to_md.py: the module to convert pdf/ppt/pptx/doc/docx files to text, jusify using pdf to image then OCR to extract text or direct text to pdf is better
3. agent.py: the module that contains the agent implementation, include the logic to check the cheat sheet coverage for lecture notes and past papers, make use of the OpenAI library to call LLM api

Put all setting under the `.env` file, including paths to directories and files, API keys, url and the model_name of LLM used, you should specific different AI model for different tasks, e.g., use gpt-5-mini for text extraction from pdf, and gpt-5 for checking coverage, you should also included a field of params for each model to specify the temperature, max_tokens, etc, it should be in json format string.

Input: 
`{course}/cheatsheet.md` or `{course}/cheatsheet.pdf`: The cheat sheet file that need to be evaluated
`{course}/lecture_notes/`: Directory containing lecture notes in .pdf or .ppt or .pptx format
`{course}/past_papers/`: Directory containing past exam papers in .pdf or .doc or .docx format
`{course}/assignment/question/`: Directory containing assignment questions in .md or .pdf or .doc format

Output:
A report in markdown format, that contains:

An checklist of important topics from lecture notes, indicating whether each topic is covered in the cheat sheet or not, if not covered, provide a brief draft of content that should be included in the cheat sheet for that topic.

An checklist of past exam questions from past papers and assignment questions, indicating whether each question can be answered with the information provided in the cheat sheet or not, if not, provide a brief draft of content that should be included in the cheat sheet to answer that question.

