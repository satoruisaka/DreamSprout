# model_registry.py
# ModelRegistry class to manage text and image generation models.
# Uses OllamaRunner for text models.
# Uses HuggingFace diffusers for image models.

from diffusers import StableDiffusionXLPipeline
import torch

class ModelRegistry:
    def __init__(self, device="cuda"):
        self.device = device
        self.text_models = {}
        self.image_models = {}

    # --- Text Models ---
    def register_text_model(self, name, model_runner):
        """Register a local LLM runner (e.g., llama.cpp, vLLM, etc.)."""
        self.text_models[name] = model_runner

    def get_text_model(self, name):
        return self.text_models.get(name)

    # --- Image Models ---
    def register_image_model(self, name, model_id, parameters, dtype=torch.float16):
        """Register a Stable Diffusion XL pipeline with config parameters."""

        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            use_safetensors=True,
            variant="fp16"
        ).to(self.device)

        pipe.enable_xformers_memory_efficient_attention()

        # Store generation parameters for later use
        pipe.generation_config = {
            "num_inference_steps": parameters.get("num_inference_steps", 30),
            "guidance_scale": parameters.get("guidance_scale", 7.5),
            "resolution": parameters.get("resolution", (768, 512)),
            "seed": parameters.get("seed", 42),
            "negative_prompt": parameters.get("negative_prompt", "")
        }

        self.image_models[name] = pipe

    def get_image_model(self, name):
        return self.image_models.get(name)


#    def register_image_model(self, name, model_id, dtype=torch.float16):
#        """Register a HuggingFace diffusers pipeline for image generation."""

#        pipe = StableDiffusionXLPipeline.from_pretrained(
#            "stabilityai/stable-diffusion-xl-base-1.0",
#        torch_dtype=torch.float16,
#        use_safetensors=True,
#        variant="fp16"
#        ).to("cuda")

#        pipe = pipe.to(self.device)
#        pipe.enable_xformers_memory_efficient_attention()
#        self.image_models[name] = pipe

