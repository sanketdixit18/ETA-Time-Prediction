
import dagshub
import mlflow

dagshub.init(
    repo_owner="sanketdixit18",
    repo_name="ETA-Time-Prediction",
    mlflow=True,
)

mlflow.set_tracking_uri(
    "https://dagshub.com/sanketdixit18/ETA-Time-Prediction.mlflow"
)

run_id = "5f2349af9f82469b8b66052ad58277d4"
model_uri = f"runs:/{run_id}/model"
registered_name = "model"

# Register the existing trained model
version = mlflow.register_model(
    model_uri=model_uri,
    name=registered_name,
)

print("\nModel registered successfully!")
print("Model name:", version.name)
print("Model version:", version.version)
print("Model status:", version.status)
