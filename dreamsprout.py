# dreamsprout.py
# Core DreamSprout functions for story generation, scene splitting,
# image prompt building, image generation, and HTML rendering.
# You can also run this as a standalone script for CLI usage for testing

import os
import argparse
import datetime
from jinja2 import Environment, FileSystemLoader
# Import DreamSprout configuration and model registry
from config import CONFIG
from model_registry import ModelRegistry
from ollama_runner import OllamaRunner

# Build the prompt for story generation
# You can modify this prompt to change the story style or requirements
def build_story_prompt(dream_input: str, core_elements: list[str]) -> str:
    return f"""
You are a fantasy storyteller for children and adults.

Write a short story (~{CONFIG['pipeline']['target_words']} words) inspired by:
- Dream: {dream_input}
- Core elements: {', '.join(core_elements)}

Requirements:
- 2nd grade level English, emotionally warm; avoid scary or dark themes.
- Use magical settings, funny characters, and surreal logic.
- End with a gentle interpretive insight.
- Include {CONFIG['pipeline']['scenes']} clear scene beats suitable for illustration.
"""

# --- Story generation ---
def generate_story(text_model_runner, dream_input: str, core_elements: list[str]) -> str:
    prompt = build_story_prompt(dream_input, core_elements)
    return text_model_runner(prompt)

# Split the story into scenes based on paragraphs
def split_scenes(story: str, desired: int) -> list[str]:
    paragraphs = [p.strip() for p in story.split("\n") if p.strip()]
    return paragraphs[:desired] if len(paragraphs) >= desired else paragraphs

# Compress scene text for illustration using the text model
def compress_scene_for_illustration(scene_text: str, text_model_runner) -> str:
    prompt = f"""
        Rewrite the following scene as a short, vivid description suitable for a storybook illustration.
        Limit to 40 words.
        Emphasize the main characters, setting, and what they’re doing.
        Use emotionally warm language that evokes visual clarity.
        Scene: {scene_text}
        Summary:"""
    return text_model_runner(prompt).strip()

# Build image prompt for a given scene
# You can modify this prompt to change the illustration style or details
def build_image_prompt(scene_text: str) -> str:
    return f"""
Illustration of a whimsical fantasy scene.
Focus: {scene_text}
Style: {CONFIG['pipeline']['style_hint']}
Mood: warm, curious, not dark
Palette: soft twilight pastels, cozy tones
Composition: clear focal subject, readable for children
"""

# Render the story and images into an HTML storybook using a Jinja2 template
def render_storybook_html(
    title: str,
    story: str,
    image_paths: list[str],
    text_model: str,
    image_model: str,
    text_prompt: str,
    image_prompts: list[str],
    timestamp: str
) -> str:    
    paragraphs = [p.strip() for p in story.split("\n") if p.strip()]
    scenes = []

    fig_index = 0
    for i, p in enumerate(paragraphs):
        image = None
        if fig_index < len(image_paths) and (i+1) % max(1, len(paragraphs)//len(image_paths)) == 0:
            image = os.path.basename(image_paths[fig_index])
            fig_index += 1
        scenes.append({"text": p, "image": image})

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("storybook_template.html")
    return template.render(
        title=title,
        scenes=scenes,
        text_model=text_model,
        image_model=image_model,
        text_prompt=text_prompt,
        image_prompts=image_prompts,
        timestamp=timestamp
    )

# Alternative simple HTML renderer without Jinja2
def render_storybook_html_alt(title: str, story: str, image_paths: list[str]) -> str:
    paragraphs = [p for p in story.split("\n") if p.strip()]
    html = [f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: "Comic Sans MS", "Comic Neue", "Trebuchet MS", sans-serif;
      font-size: 1.4em;
      line-height: 1.6;
      margin: 2em;
      padding: 2em;
      background: linear-gradient(to bottom right, #fffaf0, #e6f7ff);
      color: #333;
      border: 12px solid #f0e6d2;
      border-radius: 24px;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }}
    h1 {{
      text-align: center;
      font-size: 2em;
      margin-bottom: 1em;
    }}
    .scene {{
      margin-bottom: 3em;
    }}
    .scene img {{
      display: block;
      margin: 0 auto;
      width: 70%;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .scene p {{
      margin-top: 1em;
      text-align: center;
    }}
    a {{
      display: block;
      text-align: center;
      margin-top: 2em;
      font-size: 1em;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
"""]

    fig_index = 0
    for i, p in enumerate(paragraphs):
        html.append("<div class='scene'>")
        if fig_index < len(image_paths) and (i+1) % max(1, len(paragraphs)//len(image_paths)) == 0:
            img_name = os.path.basename(image_paths[fig_index])
            html.append(f"<img src='{img_name}' alt='Scene {fig_index+1}'/>")
            fig_index += 1
        html.append(f"<p>{p}</p>")
        html.append("</div>")

    html.append("<a href='/gallery'>Back to gallery</a>")
    html.append("</body></html>")
    return "\n".join(html)

# --- Main pipeline function ---
def run_pipeline(dream_input: str, core_elements: list[str]):
    print("\n--- Starting DreamSprout Pipeline ---")
    registry = ModelRegistry()

    # Create unique output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(CONFIG["pipeline"]["output_dir"], f"run_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    # Register Ollama text model
    print("\n--- Registering Text Model ---")
    selected_model = CONFIG["text_model"]["name"]
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
    text_model = registry.get_text_model(CONFIG["text_model"]["name"])
    story = generate_story(text_model, dream_input, core_elements)

    # Split into scenes
    print("\n--- Splitting Scenes ---")
    scenes = split_scenes(story, CONFIG["pipeline"]["scenes"])
    prompts = [build_image_prompt(s) for s in scenes]

    # Generate images
    print("\n--- Generating Images ---")
    image_model = registry.get_image_model(CONFIG["image_model"]["name"])
    print(f"Using model: {CONFIG['image_model']['name']}")  # Debug line
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

    # Render HTML
    print("\n--- Rendering HTML ---")
#    html = render_storybook_html("DreamSprout Story", story, image_paths)

    html = render_storybook_html(
        title="My Dream Story",
        story=story,
        image_paths=image_paths,
        text_model=selected_model,
        image_model=image_model,
        text_prompt=dream_input,
        image_prompts=prompts,
        timestamp=timestamp
    )

    html_path = os.path.join(output_dir, "storybook.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # --- Update index.html ---
    print("\n--- Updating Index ---")
    index_path = os.path.join(CONFIG["pipeline"]["output_dir"], "index.html")
    rel_path = os.path.relpath(html_path, CONFIG["pipeline"]["output_dir"])
    entry = f"<li><a href='{rel_path}'>{os.path.basename(output_dir)}</a></li>\n"

    if os.path.exists(index_path):
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("<h1>DreamSprout Runs</h1>\n<ul>\n")
            f.write(entry)
            f.write("</ul>\n")

    return {"story": story, "images": image_paths, "html": html_path}

# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="DreamSprout Story + Illustration Generator")
    parser.add_argument("--dream", type=str, required=True,
                        help="Dream description text")
    parser.add_argument("--elements", nargs="+", default=[],
                        help="Core elements (snake, fish, bat, etc.)")
    args = parser.parse_args()

    result = run_pipeline(dream_input=args.dream, core_elements=args.elements)

    print("\n--- DreamSprout Run Complete ---")
    print("Story saved to:", result["html"])
    print("Images generated:", result["images"])

if __name__ == "__main__":

    main()
