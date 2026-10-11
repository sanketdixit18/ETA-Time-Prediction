
# import dagshub
# import mlflow
# from mlflow import MlflowClient
# import json

# dagshub.init(
#     repo_owner="sanketdixit18",
#     repo_name="ETA-Time-Prediction",
#     mlflow=True
# )

# print("\nTracking URI:", mlflow.get_tracking_uri())

# with open("run_information.json", "r") as f:
#     run_info = json.load(f)

# model_name = run_info["model_name"]
# print("Model name from JSON:", repr(model_name))

# client = MlflowClient()

# print("\n--- Registered Models ---")
# models = client.search_registered_models()

# for registered_model in models:
#     print("Name:", repr(registered_model.name))

# print("\n--- Versions for Requested Model ---")
# try:
#     versions = client.search_model_versions(
#         f"name = '{model_name}'"
#     )

#     for version in versions:
#         print(
#             "Version:", version.version,
#             "| Stage:", version.current_stage,
#             "| Status:", version.status,
#             "| Source:", version.source
#         )

#     if not versions:
#         print("No versions found for this model name.")

# except Exception as e:
#     print(type(e).__name__, str(e))



import dagshub
import mlflow
from pathlib import Path

dagshub.init(
    repo_owner="sanketdixit18",
    repo_name="ETA-Time-Prediction",
    mlflow=True,
)

mlflow.set_tracking_uri(
    "https://dagshub.com/sanketdixit18/ETA-Time-Prediction.mlflow"
)

run_id = "5f2349af9f82469b8b66052ad58277d4"

client = mlflow.tracking.MlflowClient()

run = client.get_run(run_id)

print("Run status:", run.info.status)
print("Artifact URI:", run.info.artifact_uri)
print("\nArtifacts logged in this run:")

for item in client.list_artifacts(run_id):
    print(item.path, "| directory:", item.is_dir)

    if item.is_dir:
        for child in client.list_artifacts(run_id, item.path):
            print("  ", child.path, "| directory:", child.is_dir)
