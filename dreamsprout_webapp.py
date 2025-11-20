# dreamsprout_webapp.py
# Flask application for DreamSprout
# Handles user interactions and pipeline
# Uses DreamSprout core functions for story and image generation

import os
import threading
import datetime
from flask import Flask, request, render_template, send_from_directory, jsonify
# Import DreamSprout pipeline functions and configuration
from config import CONFIG, AVAILABLE_LLM_MODELS
from dreamsprout import compress_scene_for_illustration, run_pipeline, generate_story, split_scenes, build_image_prompt, render_storybook_html
from model_registry import ModelRegistry
from ollama_runner import OllamaRunner

# Initialize Flask app
app = Flask(__name__)
progress_tracker = {}

# Define routes
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("form.html", models=AVAILABLE_LLM_MODELS)

# Start the DreamSprout pipeline
@app.route("/start", methods=["POST"])
def start():
    dream = request.form["dream"]
    elements = request.form["elements"].split(",")
    selected_model = request.form["model"]

# Create a unique run ID using timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{timestamp}"
    output_dir = os.path.join(CONFIG["pipeline"]["output_dir"], run_id)
    os.makedirs(output_dir, exist_ok=True)

# Initialize progress tracking
    progress_tracker[run_id] = {"percent": 0, "stage": "Starting...", "done": False}

# Define the background task for the pipeline
    def background_task():
        progress_tracker[run_id].update({"percent": 5, "stage": "Registering image model..."})
        registry = ModelRegistry()
# Set up text and image generation models

# Register Ollama text model
        print("\n--- Registering Text Model ---")
        ollama_runner = OllamaRunner(model_name=selected_model)
        registry.register_text_model(selected_model, ollama_runner.generate)

# Register image model
        print("\n--- Registering Image Model ---")
        registry.register_image_model(
            CONFIG["image_model"]["name"],
            CONFIG["image_model"]["model_id"],
            CONFIG["image_model"]["parameters"]
        )

# Generate story
        print("\n--- Generating Story ---")
        progress_tracker[run_id].update({"percent": 10, "stage": "Generating story..."})
        text_model_runner = registry.get_text_model(selected_model)
        story = generate_story(text_model_runner, dream, elements)
# Split story into scenes and build image prompts
        progress_tracker[run_id].update({"percent": 30, "stage": "Splitting scenes..."})
        scenes = split_scenes(story, CONFIG["pipeline"]["scenes"])
# Compress each scene using Ollama
        compressed_scenes = [compress_scene_for_illustration(s, text_model_runner) for s in scenes]
# Build image prompts from compressed scenes
        prompts = [build_image_prompt(cs) for cs in compressed_scenes]
# Generate images for each scene
        progress_tracker[run_id].update({"percent": 60, "stage": "Creating illustrations..."})
        image_model = registry.get_image_model(CONFIG["image_model"]["name"])
        image_paths = []
        for i, p in enumerate(prompts, start=1):
            img = image_model(
                prompt=p,
                num_inference_steps=CONFIG["image_model"]["parameters"]["num_inference_steps"],
                guidance_scale=CONFIG["image_model"]["parameters"]["guidance_scale"]
            ).images[0]
            path = os.path.join(output_dir, f"scene_{i}.png")
            img.save(path)
            image_paths.append(path)
# Render storybook HTML
        progress_tracker[run_id].update({"percent": 90, "stage": "Rendering HTML..."})

        html = render_storybook_html(
            title="My Dream Story",
            story=story,
            image_paths=image_paths,
            text_model=selected_model,
            image_model=image_model,
            text_prompt=dream,
            image_prompts=prompts,
            timestamp=timestamp
        )

        with open(os.path.join(output_dir, "storybook.html"), "w", encoding="utf-8") as f:
            f.write(html)

        progress_tracker[run_id].update({"percent": 100, "stage": "Complete!", "done": True})

# Start the background task
    threading.Thread(target=background_task).start()
    return jsonify({"run_id": run_id})

# Route to check the status of a run
@app.route("/status/<run_id>")
def status(run_id):
    return jsonify(progress_tracker.get(run_id, {"percent": 0, "stage": "Starting...", "done": False}))

# Route to serve output files
@app.route("/outputs/<run_folder>/<filename>")
def serve_output(run_folder, filename):
    return send_from_directory(os.path.join("outputs", run_folder), filename)

# Route to display the gallery of past runs
@app.route("/gallery")
def gallery():
    output_root = CONFIG["pipeline"]["output_dir"]
    runs = []
    for folder in sorted(os.listdir(output_root), reverse=True):
        run_path = os.path.join(output_root, folder)
        if os.path.isdir(run_path) and "storybook.html" in os.listdir(run_path):
            runs.append({
                "name": folder,
                "link": f"/outputs/{folder}/storybook.html"
            })
    return render_template("gallery.html", runs=runs)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)