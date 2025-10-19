# app.py (frontend, Gradio) — updated to handle backend keys and pretty-print responses
import gradio as gr
import requests
from pathlib import Path
import json

BACKEND_URL = "http://127.0.0.1:8000"
current_token = None

def signup(name, email, password, contact):
    url = f"{BACKEND_URL}/signup"
    data = {
        "name": name,
        "email": email,
        "password": password,
        "contact": contact
    }
    try:
        resp = requests.post(url, json=data)
        if resp.status_code == 200:
            return "✅ Signup successful! You can now log in."
        else:
            error = resp.json().get('detail', resp.text)
            return f"❌ Signup failed: {error}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def login(email, password):
    global current_token
    url = f"{BACKEND_URL}/login"
    data = {
        "username": email,
        "password": password
    }
    try:
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            current_token = resp.json().get("access_token")
            return "✅ Login successful!", "🟢 Logged in"
        else:
            current_token = None
            error = resp.json().get('detail', resp.text)
            return f"❌ Login failed: {error}", "🔴 Not logged in"
    except Exception as e:
        current_token = None
        return f"❌ Error: {str(e)}", "🔴 Not logged in"

def review_code(file_obj):
    global current_token

    if not current_token:
        return "⚠️ Please log in first!"

    if file_obj is None:
        return "⚠️ Please upload a Python file!"

    try:
        file_path = file_obj.name
        file_name = Path(file_path).name

        url = f"{BACKEND_URL}/review"
        headers = {"Authorization": f"Bearer {current_token}"}

        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'text/x-python')}
            response = requests.post(url, headers=headers, files=files, timeout=120)

        if response.status_code == 200:
            result = response.json()

            output_lines = ["## Code Review Results\n"]

            # Backend uses "ai_result" in main.py; be flexible and check for multiple keys
            ai_review = result.get('ai_review') or result.get('ai_result') or result.get('gemini_review')
            if ai_review:
                output_lines.append("### 🤖 AI Analysis")
                if isinstance(ai_review, (list, dict)):
                    output_lines.append("```json\n" + json.dumps(ai_review, indent=2) + "\n```")
                else:
                    output_lines.append(str(ai_review))

            static_analysis = result.get('static_analysis') or result.get('static_result')
            if static_analysis:
                output_lines.append("\n### 🔍 Static Analysis")
                output_lines.append("```\n" + static_analysis + "\n```")

            return "\n".join(output_lines)
        else:
            # include JSON error if available
            try:
                return f"❌ Review failed: {response.json()}"
            except Exception:
                return f"❌ Review failed: {response.text}"

    except Exception as e:
        import traceback
        return f"❌ Error during review: {str(e)}\n\n```\n{traceback.format_exc()}\n```"

def clear_outputs():
    return [None, "", "", ""]

# Gradio UI (unchanged structure)
with gr.Blocks(title="AI Code Review Assistant") as demo:
    gr.Markdown("# AI Code Review Assistant\nUpload your Python code for AI-powered review and analysis.")
    login_status = gr.Markdown("🔴 Not logged in")

    with gr.Tabs():
        with gr.TabItem("Sign Up"):
            with gr.Column():
                name_input = gr.Textbox(label="Name")
                email_input = gr.Textbox(label="Email")
                password_input = gr.Textbox(label="Password", type="password")
                contact_input = gr.Textbox(label="Contact")
                signup_btn = gr.Button("Sign Up", variant="primary")
                signup_output = gr.Markdown()
                signup_btn.click(signup, inputs=[name_input, email_input, password_input, contact_input], outputs=signup_output)

        with gr.TabItem("Login"):
            with gr.Column():
                login_email = gr.Textbox(label="Email")
                login_password = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Login", variant="primary")
                login_output = gr.Markdown()
                login_btn.click(login, inputs=[login_email, login_password], outputs=[login_output, login_status])

        with gr.TabItem("Code Review"):
            with gr.Column():
                gr.Markdown("### Submit Code for Review\n1. Login\n2. Upload a .py file\n3. Click 'Review Code'")
                file_input = gr.File(label="Upload Python File", file_types=[".py"], type="filepath")
                with gr.Row():
                    review_btn = gr.Button("Review Code", variant="primary")
                    clear_btn = gr.Button("Clear", variant="secondary")
                review_output = gr.Markdown()
                review_btn.click(fn=review_code, inputs=[file_input], outputs=review_output)
                clear_btn.click(fn=lambda: None, inputs=[], outputs=review_output)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)