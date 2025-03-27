# IntelliQuiz - AI-Powered Learning Material Generator

IntelliQuiz is an AI-powered platform designed to generate personalized learning materials such as quizzes and coding exercises based on input content. You can upload PDFs, paste text, and provide specific instructions to generate relevant quizzes and coding exercises in a variety of programming languages.

## Features

- **Multiple Choice Quiz Generator**: Generates quizzes with multiple-choice questions from provided text content or uploaded PDF files.
- **Programming Exercises Generator**: Creates coding exercises in different programming languages with varying levels of difficulty.
- **PDF Text Extraction**: Extracts text content from PDFs for quiz or exercise generation.
- **Customizable Settings**: Users can define quiz difficulty, number of questions, programming language, and exercise difficulty.


### Website

https://intelliquiz.streamlit.app/


### How to run the app locally

1. Clone the repository
2. Create a .env file in the root directory and add OPENAI_API_KEY = "your openai api key" to it.
3. Create a virtual environment and activate it.
4. in the root directory, install the required Python packages: run: 
    ```bash
    pip install -r requirements.txt
    ```
5. in the root directory, run the Streamlit application:

    ```bash
    streamlit run app.py
    ```
