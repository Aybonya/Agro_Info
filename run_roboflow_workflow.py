# 1. Import the library
import json
import sys
from pathlib import Path
from inference_sdk import InferenceHTTPClient, InferenceConfiguration

# 2. Connect to your workflow
client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="T6sW80zFrGiFCA9k112V"
).configure(InferenceConfiguration(
    api_key_transport="header"  # header-based auth (inference v1.5.0+)
))

# 3. Get image path from arguments or default to Auto/1.jpg
image_path = sys.argv[1] if len(sys.argv) > 1 else "Auto/1.jpg"
if not Path(image_path).exists():
    print(f"File not found: {image_path}")
    sys.exit(1)

print(f"Running workflow for: {image_path} ...")

# 4. Run inference using your latest trained Roboflow model (v6)
result = client.infer(
    image_path,
    model_id="trucks-dataset-dqp47/6"
)

# 5. Get your results
print("\n--- Результаты детекции Roboflow ---")
print(json.dumps(result, indent=2, ensure_ascii=False))
