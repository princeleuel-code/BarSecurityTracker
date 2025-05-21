# Model Weights for YOLOv8-Thermal-Attn

This directory is intended to store the ONNX model weights for the YOLOv8-Thermal-Attn detector.

The current placeholder file `y8_thermal.onnx` is an empty file for development and testing purposes.

## TODO: Handling Large Model Files

When an actual ONNX model is used, it may be too large for direct storage in the Git repository. The following strategies should be considered:

1.  **Git LFS (Large File Storage):**
    *   Initialize Git LFS in the repository (`git lfs install`).
    *   Track the ONNX file type (`git lfs track "*.onnx"`).
    *   Ensure `.gitattributes` is committed.
    *   Users will need Git LFS installed to clone and pull the actual model file.

2.  **Download Script:**
    *   Provide a script (e.g., `download_model.sh` or a Python script) that fetches the model from a remote location (e.g., a release asset, cloud storage bucket, Hugging Face Hub).
    *   This script could be called during the Docker build process (if the model needs to be baked into the image) or as a manual setup step.
    *   The `compose.yaml` volume mount for weights (`./src/detectors/y8_thermal/weights:/app/y8_thermal/weights`) would work well if the script downloads the model to the local `./src/detectors/y8_thermal/weights` directory before `docker compose up`.

Choose one of these strategies when replacing the placeholder `y8_thermal.onnx` with a real model to keep the core repository lightweight and manageable.
