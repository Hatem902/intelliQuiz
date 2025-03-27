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

@st.cache_data
def fetch_coding_exercises(text_content, user_prompt, programming_language, difficulty, num_exercises):
    """Generate coding exercises based on input content."""
    RESPONSE_JSON = {
      "exercises": [
        {
            "problem": "Description of the programming problem",
            "difficulty": "Easy/Medium/Hard",
            "input": "Example input",
            "output": "Expected output",
            "solution": "Example solution code",
            "explanation": "Detailed explanation of the solution"
        }
      ] * num_exercises
    }

    PROMPT_TEMPLATE = f"""
    Text: {text_content}
    
    User Instructions: {user_prompt}
    
    You are an expert in generating programming exercises based on provided content.
    Given the above text, create {num_exercises} coding exercises in {programming_language} with {difficulty} difficulty.
    Ensure that each exercise has:
    - A clear problem statement
    - Matching difficulty level
    - Example input
    - Expected output
    - A correct solution
    - A detailed explanation of the solution approach
    
    Respond ONLY in the following JSON format:
    ```json
    {json.dumps(RESPONSE_JSON, indent=4)}
    ```
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": PROMPT_TEMPLATE}],
        temperature=0.3,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={"type": "json_object"}
    )

    extracted_response = response.choices[0].message.content
    
    try:
        return json.loads(extracted_response).get("exercises", [])
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error: {e}")
        return []

def generate_quiz(content, user_prompt, quiz_level, num_questions):
    """Render quiz generation interface and logic."""
    st.subheader("Quiz Questions")
    st.session_state.selected_options = [None] * len(st.session_state.questions)
    
    for i, question in enumerate(st.session_state.questions):
        st.markdown(f"**Q{i+1}: {question['mcq']}**")
        options = list(question["options"].values())
        option_keys = list(question["options"].keys())
        
        selected_index = st.radio(
            f"Select your answer for question {i+1}:",
            options,
            key=f"q{i}",
            index=None
        )
        
        if selected_index is not None:
            selected_idx = options.index(selected_index)
            st.session_state.selected_options[i] = option_keys[selected_idx]
        
        st.markdown("---")
    
    if st.button("Submit Quiz"):
        st.header("Quiz Results:")
        marks = 0
        
        for i, question in enumerate(st.session_state.questions):
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
        
        percentage = (marks / len(st.session_state.questions)) * 100
        st.subheader(f"Final Score: {marks} out of {len(st.session_state.questions)} ({percentage:.1f}%)")
        
        if st.button("Create New Learning Material"):
            st.session_state.material_generated = False
            st.experimental_rerun()


def generate_coding_exercises(content, user_prompt, programming_language, difficulty, num_exercises):
    """Render coding exercise generation interface and logic."""
    st.subheader(f"Generated {difficulty} Exercises")
    
    for i, exercise in enumerate(st.session_state.exercises):
        # Display difficulty badge
        difficulty_color = {
            "Easy": "green",
            "Medium": "orange",
            "Hard": "red"
        }.get(exercise.get('difficulty', difficulty), "blue")
        
        st.markdown(f"**Exercise {i+1}**: {exercise['problem']} "
                    f"<span style='color:{difficulty_color};'>({exercise.get('difficulty', difficulty)} Difficulty)</span>", 
                    unsafe_allow_html=True)
        
        st.code(f"Input: {exercise['input']}\nExpected Output: {exercise['output']}", language="text")
        
        with st.expander("💡 Show Solution"):
            st.code(exercise["solution"], language=programming_language.lower())
            st.markdown("**📝 Explanation:**")
            st.markdown(exercise.get("explanation", "No detailed explanation available."))
        
        st.markdown("---")

def main():
    st.markdown("""
        # IntelliQuizz  
        ### AI-Powered Quizzes, Programming Exercises, Tailored to Your Content in Seconds! &nbsp;  
    """,)
    
    # Select mode of generation
    learning_mode = st.radio(
        "Choose the type of learning material you want to generate:",
        ["Multiple Choice Quiz", "Programming Exercises"]
    )
    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF file containing course material", type="pdf")
    
    # Text input as an alternative to PDF upload
    text_content = st.text_area("Or paste the text content here:")
    
    # User prompt for customization
    user_prompt = st.text_area("Instructions for quiz generation (e.g., 'Focus on key concepts', 'Include definitions', etc.):", 
                              placeholder="Example: Focus on chapter 3 and include questions about the main theories")
    
    # Quiz parameters
    if learning_mode == "Multiple Choice Quiz":
        col1, col2 = st.columns(2)
        with col1:
            quiz_level = st.selectbox("Select quiz difficulty:", ["Easy", "Medium", "Hard"])
        with col2:
            num_questions = st.slider("Number of questions:", min_value=1, max_value=10, value=3)
    else:  # Programming Exercises
        col1, col2, col3 = st.columns(3)
        with col1:
            programming_language = st.selectbox("Select programming language:", 
                                                ["Python", "Java", "C++", "JavaScript"])
        with col2:
            difficulty = st.selectbox("Select difficulty:", 
                                      ["Easy", "Medium", "Hard"])
        with col3:
            num_exercises = st.slider("Number of exercises:", min_value=1, max_value=10, value=3)
    



    # Initialize session_state
      # Initialisation des variables de session
    if 'material_generated' not in st.session_state:
        st.session_state.material_generated = False
    if 'content_processed' not in st.session_state:
        st.session_state.content_processed = None

    # Traitement du fichier PDF
    if uploaded_file is not None and st.session_state.content_processed != uploaded_file.name:
        with st.spinner("Processing PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text.strip():
                st.session_state.content = pdf_text
                st.session_state.content_processed = uploaded_file.name
                st.success(f"PDF processed: {len(pdf_text.split())} words extracted")
            else:
                st.error("Could not extract text from the PDF. Please try another file.")
    
    # Utiliser le texte collé si aucun fichier PDF n'est téléchargé
    if not uploaded_file and text_content:
        st.session_state.content = text_content

    # Bouton pour générer le matériel
    generate_button = st.button("Generate Learning Material", key="generate_button")

    # Lors du clic sur le bouton
    if generate_button:
        if not hasattr(st.session_state, 'content') or not st.session_state.content:
            st.error("Please upload a PDF or enter text content to generate learning material.")
        else:
            # Génère le matériel et marque l'état
            st.session_state.material_generated = True
            st.session_state.content_processed = None  # Reset content to allow file change

    # Génération du matériel en fonction du mode sélectionné
    if st.session_state.material_generated and hasattr(st.session_state, 'content'):
        if learning_mode == "Multiple Choice Quiz":
            with st.spinner(f"Generating {num_questions} {quiz_level} difficulty questions..."):
                questions = fetch_questions(
                    text_content=st.session_state.content,
                    user_prompt=user_prompt,
                    quiz_level=quiz_level.lower(),
                    num_questions=num_questions
                )

                if not questions:
                    st.error("Failed to generate questions. Please try again.")
                    st.session_state.material_generated = False
                    return

                st.session_state.questions = questions
                generate_quiz(
                    content=st.session_state.content, 
                    user_prompt=user_prompt, 
                    quiz_level=quiz_level, 
                    num_questions=num_questions
                )

        else:  # Exercices de programmation
            with st.spinner(f"Generating {num_exercises} {difficulty} exercises in {programming_language}..."):
                exercises = fetch_coding_exercises(
                    text_content=st.session_state.content,
                    user_prompt=user_prompt,
                    programming_language=programming_language,
                    difficulty=difficulty,
                    num_exercises=num_exercises
                )

                if not exercises:
                    st.error("Failed to generate exercises. Please try again.")
                    st.session_state.material_generated = False
                    return

                st.session_state.exercises = exercises
                generate_coding_exercises(
                    content=st.session_state.content,
                    user_prompt=user_prompt,
                    programming_language=programming_language,
                    difficulty=difficulty,
                    num_exercises=num_exercises
                )


if __name__ == "__main__":
    main()