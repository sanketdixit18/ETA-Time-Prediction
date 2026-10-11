
import dagshub
import mlflow
from mlflow import MlflowClient
import json

dagshub.init(
    repo_owner="sanketdixit18",
    repo_name="ETA-Time-Prediction",
    mlflow=True
)

print("\nTracking URI:", mlflow.get_tracking_uri())

with open("run_information.json", "r") as f:
    run_info = json.load(f)

model_name = run_info["model_name"]
print("Model name from JSON:", repr(model_name))

client = MlflowClient()

print("\n--- Registered Models ---")
models = client.search_registered_models()

for registered_model in models:
    print("Name:", repr(registered_model.name))

print("\n--- Versions for Requested Model ---")
try:
    versions = client.search_model_versions(
        f"name = '{model_name}'"
    )

    for version in versions:
        print(
            "Version:", version.version,
            "| Stage:", version.current_stage,
            "| Status:", version.status,
            "| Source:", version.source
        )

    if not versions:
        print("No versions found for this model name.")

except Exception as e:
    print(type(e).__name__, str(e))
