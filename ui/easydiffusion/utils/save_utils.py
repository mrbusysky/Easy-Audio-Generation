import os
import time
import re

from easydiffusion.types import TaskData, GenerateImageRequest

from sdkit.utils import save_images, save_dicts
from numpy import base_repr

filename_regex = re.compile("[^a-zA-Z0-9._-]")

# keep in sync with `ui/media/js/dnd.js`
TASK_TEXT_MAPPING = {
    "prompt": "Prompt",
    "width": "Width",
    "height": "Height",
    "seed": "Seed",
    "num_inference_steps": "Steps",
    "guidance_scale": "Guidance Scale",
    "prompt_strength": "Prompt Strength",
    "use_face_correction": "Use Face Correction",
    "use_upscale": "Use Upscaling",
    "upscale_amount": "Upscale By",
    "sampler_name": "Sampler",
    "negative_prompt": "Negative Prompt",
    "use_stable_diffusion_model": "Stable Diffusion model",
    "use_vae_model": "VAE model",
    "use_hypernetwork_model": "Hypernetwork model",
    "hypernetwork_strength": "Hypernetwork Strength",
    "use_lora_model": "LoRA model",
    # "lora_alpha": "LoRA Strength",
}


def save_images_to_disk(images: list, filtered_images: list, req: GenerateImageRequest, task_data: TaskData):
    now = time.time()
    save_dir_path = os.path.join(task_data.save_to_disk_path, filename_regex.sub("_", task_data.session_id))
    metadata_entries = get_metadata_entries_for_request(req, task_data)
    make_filename = make_filename_callback(req, now=now)

    if task_data.show_only_filtered_image or filtered_images is images:
        save_images(
            filtered_images,
            save_dir_path,
            file_name=make_filename,
            output_format=task_data.output_format,
            output_quality=task_data.output_quality,
        )
        if task_data.metadata_output_format.lower() in ["json", "txt", "embed"]:
            save_dicts(
                metadata_entries,
                save_dir_path,
                file_name=make_filename,
                output_format=task_data.metadata_output_format,
                file_format=task_data.output_format,
            )
    else:
        make_filter_filename = make_filename_callback(req, now=now, suffix="filtered")

        save_images(
            images,
            save_dir_path,
            file_name=make_filename,
            output_format=task_data.output_format,
            output_quality=task_data.output_quality,
        )
        save_images(
            filtered_images,
            save_dir_path,
            file_name=make_filter_filename,
            output_format=task_data.output_format,
            output_quality=task_data.output_quality,
        )
        if task_data.metadata_output_format.lower() in ["json", "txt", "embed"]:
            save_dicts(
                metadata_entries,
                save_dir_path,
                file_name=make_filter_filename,
                output_format=task_data.metadata_output_format,
                file_format=task_data.output_format,
            )


def get_metadata_entries_for_request(req: GenerateImageRequest, task_data: TaskData):
    metadata = get_printable_request(req)
    metadata.update(
        {
            "use_stable_diffusion_model": task_data.use_stable_diffusion_model,
            "use_vae_model": task_data.use_vae_model,
            "use_hypernetwork_model": task_data.use_hypernetwork_model,
            "use_lora_model": task_data.use_lora_model,
            "use_face_correction": task_data.use_face_correction,
            "use_upscale": task_data.use_upscale,
        }
    )
    if metadata["use_upscale"] is not None:
        metadata["upscale_amount"] = task_data.upscale_amount
    if task_data.use_hypernetwork_model is None:
        del metadata["hypernetwork_strength"]
    if task_data.use_lora_model is None:
        if "lora_alpha" in metadata:
            del metadata["lora_alpha"]

        from easydiffusion import app

        app_config = app.getConfig()
        if not app_config.get("test_diffusers", False) and "use_lora_model" in metadata:
            del metadata["use_lora_model"]

    # if text, format it in the text format expected by the UI
    is_txt_format = task_data.metadata_output_format.lower() == "txt"
    if is_txt_format:
        metadata = {TASK_TEXT_MAPPING[key]: val for key, val in metadata.items() if key in TASK_TEXT_MAPPING}

    entries = [metadata.copy() for _ in range(req.num_outputs)]
    for i, entry in enumerate(entries):
        entry["Seed" if is_txt_format else "seed"] = req.seed + i

    return entries


def get_printable_request(req: GenerateImageRequest):
    metadata = req.dict()
    del metadata["init_image"]
    del metadata["init_image_mask"]
    if req.init_image is None:
        del metadata["prompt_strength"]
    return metadata


def make_filename_callback(req: GenerateImageRequest, suffix=None, now=None):
    if now is None:
        now = time.time()

    def make_filename(i):
        img_id = base_repr(int(now * 10000), 36)[-7:] + base_repr(int(i),36)  # Base 36 conversion, 0-9, A-Z

        prompt_flattened = filename_regex.sub("_", req.prompt)[:50]
        name = f"{prompt_flattened}_{img_id}"
        name = name if suffix is None else f"{name}_{suffix}"
        return name

    return make_filename
