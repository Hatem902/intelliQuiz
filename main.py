import streamlit as st
import json
import os
from dotenv import load_dotenv
import PyPDF2
import io

load_dotenv()  # Load all the environment variables from .env file

from openai import OpenAI
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

@st.cache_data
def extract_text_from_pdf(pdf_file):
    """Extract text content from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

@st.cache_data
def fetch_questions(text_content, user_prompt, quiz_level, num_questions):
    # Define the expected response format with dynamic number of questions
    RESPONSE_JSON = {
      "mcqs": [
        {
            "mcq": "multiple choice question",
            "options": {
                "a": "choice here",
                "b": "choice here",
                "c": "choice here",
                "d": "choice here",
            },
            "correct": "correct choice option in the form of a, b, c or d",
        }
      ] * num_questions  # This creates a list with the template repeated num_questions times
    }

    PROMPT_TEMPLATE = """
    Text: {text_content}
    
    User Instructions: {user_prompt}
    
    You are an expert in generating MCQ type quiz on the basis of provided content.
    Given the above text, create a quiz of {num_questions} multiple choice questions keeping difficulty level as {quiz_level}.
    Follow the user's instructions when creating the quiz: {user_prompt}
    
    Make sure the questions are not repeated and check all the questions to be conforming to the text as well.
    Make sure to format your response like RESPONSE_JSON below and use it as a guide.
    Ensure to make an array of {num_questions} MCQs referring to the following response json.
    
    Here is the RESPONSE_JSON: 

    {RESPONSE_JSON}
    """

    formatted_template = PROMPT_TEMPLATE.format(
        text_content=text_content, 
        user_prompt=user_prompt,
        quiz_level=quiz_level, 
        num_questions=num_questions,
        RESPONSE_JSON=RESPONSE_JSON
    )

    # Make API request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": formatted_template
            }
        ],
        temperature=0.3,
        max_tokens=2000,  # Increased to accommodate more questions
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Extract response JSON
    extracted_response = response.choices[0].message.content

    try:
        return json.loads(extracted_response).get("mcqs", [])
    except json.JSONDecodeError:
        st.error("Failed to parse the response. Please try again.")
        return []

def main():
    st.title("Advanced Quiz Generator App")

    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF file containing course material", type="pdf")
    
    # Text input as an alternative to PDF upload
    text_content = st.text_area("Or paste the text content here:")
    
    # User prompt for customization
    user_prompt = st.text_area("Instructions for quiz generation (e.g., 'Focus on key concepts', 'Include definitions', etc.):", 
                              placeholder="Example: Focus on chapter 3 and include questions about the main theories")
    
    # Quiz parameters
    col1, col2 = st.columns(2)
    with col1:
        quiz_level = st.selectbox("Select quiz difficulty:", ["Easy", "Medium", "Hard"])
    with col2:
        num_questions = st.slider("Number of questions:", min_value=1, max_value=10, value=3)
    
    # Convert quiz level to lower casing
    quiz_level_lower = quiz_level.lower()

    # Initialize session_state
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    
    if 'content_processed' not in st.session_state:
        st.session_state.content_processed = None
    
    # Extract content from PDF if uploaded
    if uploaded_file is not None and st.session_state.content_processed != uploaded_file.name:
        with st.spinner("Processing PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text.strip():
                st.session_state.content = pdf_text
                st.session_state.content_processed = uploaded_file.name
                st.success(f"PDF processed: {len(pdf_text.split())} words extracted")
            else:
                st.error("Could not extract text from the PDF. Please try another file.")
    
    # Use text area content if PDF isn't uploaded or is empty
    if not uploaded_file and text_content:
        st.session_state.content = text_content
    
    # Button to generate quiz
    generate_button = st.button("Generate Quiz")
    
    if generate_button:
        if not hasattr(st.session_state, 'content') or not st.session_state.content:
            st.error("Please upload a PDF or enter text content to generate a quiz.")
        else:
            st.session_state.quiz_generated = True
            
    if st.session_state.quiz_generated and hasattr(st.session_state, 'content'):
        with st.spinner(f"Generating {num_questions} {quiz_level_lower} difficulty questions..."):
            # Generate questions based on the content, prompt, level, and count
            questions = fetch_questions(
                text_content=st.session_state.content,
                user_prompt=user_prompt,
                quiz_level=quiz_level_lower,
                num_questions=num_questions
            )
            
            if not questions:
                st.error("Failed to generate questions. Please try again.")
                st.session_state.quiz_generated = False
                return
            
            # Store questions in session state
            st.session_state.questions = questions
            
            # Display questions and radio buttons
            st.subheader("Quiz Questions")
            st.session_state.selected_options = [None] * len(questions)
            
            for i, question in enumerate(questions):
                st.markdown(f"**Q{i+1}: {question['mcq']}**")
                options = list(question["options"].values())
                option_keys = list(question["options"].keys())
                
                # Create unique key for each radio button
                selected_index = st.radio(
                    f"Select your answer for question {i+1}:",
                    options,
                    key=f"q{i}",
                    index=None
                )
                
                # Store the selected option
                if selected_index is not None:
                    selected_idx = options.index(selected_index)
                    st.session_state.selected_options[i] = option_keys[selected_idx]
                
                st.markdown("---")
                
            # Submit button
            if st.button("Submit Quiz"):
                st.header("Quiz Results:")
                marks = 0
                
                for i, question in enumerate(questions):
                    selected_option_key = st.session_state.selected_options[i]
                    correct_option_key = question["correct"]
                    
                    st.markdown(f"**Q{i+1}: {question['mcq']}**")
                    
                    if selected_option_key:
                        st.write(f"You selected: {question['options'][selected_option_key]}")
                    else:
                        st.write("You didn't select an answer")
                        
                    st.write(f"Correct answer: {question['options'][correct_option_key]}")
                    
                    if selected_option_key == correct_option_key:
                        marks += 1
                        st.success("Correct! ✓")
                    else:
                        st.error("Incorrect ✗")
                        
                    st.markdown("---")
                    
                # Display final score
                percentage = (marks / len(questions)) * 100
                st.subheader(f"Final Score: {marks} out of {len(questions)} ({percentage:.1f}%)")
                
                # Reset button
                if st.button("Create New Quiz"):
                    st.session_state.quiz_generated = False
                    st.experimental_rerun()

if __name__ == "__main__":
    main()