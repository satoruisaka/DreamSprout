# config.py
# DreamSprout configuration settings for text and image models,
# pipeline parameters, and file management.

# File locations
OUTPUT_DIR = "outputs"

# Ollama settings - 
OLLAMA_URL = "http://localhost:11434/api/generate"

# Available text models for user to select in the web app
# Make sure these models are downloaded and installed in your Ollama server
AVAILABLE_LLM_MODELS = [
    "dolphin3",
    "gemma3:4b",
    "llama3.1",
    "mistral",
    "openchat",
    "phi3:14b",
    "qwen3"
]

CONFIG = {
    "text_model": { # text model configuration
        "name": "llama3.1", # default model name for OllamaRunner
        "backend": "ollama",
        "parameters": {
            "num_ctx": 32000, # [IMPORTANT] set the context window size high
            "max_tokens": 32000,
            "temperature": 0.8,
            "top_p": 0.9
        }
    },

    "image_model": { # image model configuration
        "name": "sdxl",
        "backend": "diffusers",
        "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "parameters": {
            "dtype": "float16", # torch dtype
            "num_inference_steps": 30,
            "guidance_scale": 6.5,
            "resolution": (768, 512),
            "seed": 42,
            "negative_prompt": "scary, horror, gore, photorealistic, harsh shadows, text overlay"
        }
    },

    "pipeline": { # pipeline configuration
        "target_words": 500,
        "scenes": 4,
        "style_hint": "gentle, whimsical, storybook illustration",
        "output_dir": OUTPUT_DIR,
        "format": "html"
    }
}