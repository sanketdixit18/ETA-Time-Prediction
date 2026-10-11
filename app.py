# from pathlib import Path
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi import FastAPI, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel
# from sklearn.pipeline import Pipeline
# import uvicorn
# import pandas as pd
# import mlflow
# import json
# import joblib
# import os
# from mlflow import MlflowClient
# from sklearn import set_config
# from scripts.data_clean_utils import perform_data_cleaning



# # create the app
# app = FastAPI(title="ETA Time Prediction")

# # folder that holds this file, so static/templates resolve from any working directory
# BASE_DIR = Path(__file__).resolve().parent

# # Mount static files (css, js)
# app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# # Templates setup
# templates = Jinja2Templates(directory=BASE_DIR / "templates")

# # create the home endpoint
# @app.get(path="/")
# def home(request: Request):
#     return templates.TemplateResponse(
#         request,
#         "home.html",
#         {"model_name": model_name, "stage": stage},
#     )
   


# # set the output as pandas
# set_config(transform_output='pandas')

# # initialize dagshub
# import dagshub
# import mlflow.client

# dagshub.init(repo_owner='sanketdixit18',
#               repo_name='ETA-Time-Prediction',
#                 mlflow=True)


# # set the mlflow tracking server
# mlflow.set_tracking_uri("https://dagshub.com/sanketdixit18/ETA-Time-Prediction.mlflow")


# class Data(BaseModel):  
#     ID: str
#     Delivery_person_ID: str
#     Delivery_person_Age: str
#     Delivery_person_Ratings: str
#     Restaurant_latitude: float
#     Restaurant_longitude: float
#     Delivery_location_latitude: float
#     Delivery_location_longitude: float
#     Order_Date: str
#     Time_Orderd: str
#     Time_Order_picked: str
#     Weatherconditions: str
#     Road_traffic_density: str
#     Vehicle_condition: int
#     Type_of_order: str
#     Type_of_vehicle: str
#     multiple_deliveries: str
#     Festival: str
#     City: str


    
    
# def load_model_information(file_path):
#     with open(file_path) as f:
#         run_info = json.load(f)
        
#     return run_info


# def load_transformer(transformer_path):
#     transformer = joblib.load(transformer_path)
#     return transformer



# # columns to preprocess in data
# num_cols = ["age",
#             "ratings",
#             "pickup_time_minutes",
#             "distance"]

# nominal_cat_cols = ['weather',
#                     'type_of_order',
#                     'type_of_vehicle',
#                     "festival",
#                     "city_type",
#                     "is_weekend",
#                     "order_time_of_day"]

# ordinal_cat_cols = ["traffic","distance_type"]

# #mlflow client
# client = MlflowClient()

# # load the model info to get the model name
# model_name = load_model_information("run_information.json")['model_name']

# # stage of the model
# stage = "Staging"

# # get the latest model version
# # latest_model_ver = client.get_latest_versions(name=model_name,stages=[stage])
# # print(f"Latest model in production is version {latest_model_ver[0].version}")

# # load model path
# model_path = f"models:/{model_name}/{stage}"

# # load the latest model from model registry
# model = mlflow.sklearn.load_model(model_path)
# print("Model loaded successfully from DagsHub. Server is starting...")

# # load the preprocessor
# preprocessor_path = "models/preprocessor.joblib"
# preprocessor = load_transformer(preprocessor_path)

# # build the model pipeline
# model_pipe = Pipeline(steps=[
#     ('preprocess',preprocessor),
#     ("regressor",model)
# ])

# # create the app
# app = FastAPI()

# # Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Templates setup
# templates = Jinja2Templates(directory="templates")


# # create the home endpoint
# @app.get(path="/")
# def home(request: Request):
#     return templates.TemplateResponse("home.html", {
#         "request": request,
#         "model_name": model_name,
#         "stage": stage
#     })

# # create the predict endpoint
# @app.post(path="/predict")
# def do_predictions(data: Data):
#     pred_data = pd.DataFrame(
#         { 'ID': data.ID,
#         'Delivery_person_ID': data.Delivery_person_ID,
#         'Delivery_person_Age': data.Delivery_person_Age,
#         'Delivery_person_Ratings': data.Delivery_person_Ratings,
#         'Restaurant_latitude': data.Restaurant_latitude,
#         'Restaurant_longitude': data.Restaurant_longitude,
#         'Delivery_location_latitude': data.Delivery_location_latitude,
#         'Delivery_location_longitude': data.Delivery_location_longitude,
#         'Order_Date': data.Order_Date,
#         'Time_Orderd': data.Time_Orderd,
#         'Time_Order_picked': data.Time_Order_picked,
#         'Weatherconditions': data.Weatherconditions,
#         'Road_traffic_density': data.Road_traffic_density,
#         'Vehicle_condition': data.Vehicle_condition,
#         'Type_of_order': data.Type_of_order,
#         'Type_of_vehicle': data.Type_of_vehicle,
#         'multiple_deliveries': data.multiple_deliveries,
#         'Festival': data.Festival,
#         'City': data.City
#         },index=[0]
        
#     )
#     # clean the raw input data
#     cleaned_data = perform_data_cleaning(pred_data)
#     # get the predictions
#     predictions = model_pipe.predict(cleaned_data)[0]

#     return predictions

#     # clean the raw input data
#     try:
#         cleaned_data = perform_data_cleaning(pred_data)
#     except (ValueError, TypeError, KeyError) as exc:
#         raise HTTPException(status_code=422, detail=f"Invalid input: {exc}")

#     # the cleaning step drops rows it cannot use (e.g. a route longer than 25 km,
#     # coordinates below 1, orders placed between 00:00 and 00:59, riders under 18)
#     if cleaned_data.empty:
#         raise HTTPException(
#             status_code=422,
#             detail="These inputs are outside what the model supports. Check the "
#                    "rider age (18+), the route (under 25 km), the coordinates "
#                    "and the order time (not between 00:00 and 00:59).",
#         )

#     # get the predictions
#     predictions = model_pipe.predict(cleaned_data)[0]

#     return float(predictions)



# if __name__ == "__main__":
#     uvicorn.run(app="app:app",host="0.0.0.0",port=8000)





from pathlib import Path
import json

import dagshub
import joblib
import mlflow
import pandas as pd
import uvicorn

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mlflow import MlflowClient
from pydantic import BaseModel
from sklearn import set_config
from sklearn.pipeline import Pipeline

from scripts.data_clean_utils import perform_data_cleaning


# ==================================================
# 1. Application configuration
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="ETA Time Prediction",
    description="Delivery time prediction API using Machine Learning",
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

set_config(transform_output="pandas")


# ==================================================
# 2. DagsHub and MLflow configuration
# ==================================================

dagshub.init(
    repo_owner="sanketdixit18",
    repo_name="ETA-Time-Prediction",
    mlflow=True,
)

mlflow.set_tracking_uri(
    "https://dagshub.com/sanketdixit18/ETA-Time-Prediction.mlflow"
)

client = MlflowClient()


# ==================================================
# 3. Load model information
# ==================================================

def load_model_information(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_transformer(file_path: Path):
    return joblib.load(file_path)


run_info_path = BASE_DIR / "run_information.json"
preprocessor_path = BASE_DIR / "models" / "preprocessor.joblib"

if not run_info_path.exists():
    raise FileNotFoundError(
        f"Model information file not found: {run_info_path}"
    )

if not preprocessor_path.exists():
    raise FileNotFoundError(
        f"Preprocessor file not found: {preprocessor_path}"
    )

run_info = load_model_information(run_info_path)

model_name = run_info["model_name"]
model_version = "1"

model_path = f"models:/{model_name}/{model_version}"

print(f"Loading model: {model_name}, version {model_version}")

try:
    model = mlflow.sklearn.load_model(model_path)
except Exception as exc:
    raise RuntimeError(
        f"Failed to load MLflow model '{model_name}', "
        f"version '{model_version}'. Check DagsHub access "
        "and the registered model version."
    ) from exc

print("MLflow model loaded successfully.")

preprocessor = load_transformer(preprocessor_path)

model_pipe = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("regressor", model),
    ]
)

print("Prediction pipeline initialized successfully.")


# ==================================================
# 4. Request schema
# ==================================================

class Data(BaseModel):
    ID: str
    Delivery_person_ID: str
    Delivery_person_Age: str
    Delivery_person_Ratings: str

    Restaurant_latitude: float
    Restaurant_longitude: float

    Delivery_location_latitude: float
    Delivery_location_longitude: float

    Order_Date: str
    Time_Orderd: str
    Time_Order_picked: str

    Weatherconditions: str
    Road_traffic_density: str
    Vehicle_condition: int

    Type_of_order: str
    Type_of_vehicle: str
    multiple_deliveries: str
    Festival: str
    City: str


# ==================================================
# 5. Home page
# ==================================================

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "model_name": model_name,
            "model_version": model_version,
            "stage": "Registered Model",
        },
    )


# ==================================================
# 6. Health check
# ==================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_name": model_name,
        "model_version": model_version,
    }


# ==================================================
# 7. Prediction endpoint
# ==================================================

@app.post("/predict")
def do_predictions(data: Data):

    # Convert incoming data into a single-row DataFrame
    pred_data = pd.DataFrame(
        [data.model_dump()]
    )

    # Clean and validate input
    try:
        cleaned_data = perform_data_cleaning(pred_data)

    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid input: {exc}",
        ) from exc

    if cleaned_data is None or cleaned_data.empty:
        raise HTTPException(
            status_code=422,
            detail=(
                "Input data cannot be used for prediction. "
                "Check rider age, route distance, coordinates, "
                "and order time against the supported data range."
            ),
        )

    # Predict ETA
    try:
        prediction = model_pipe.predict(cleaned_data)[0]

    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Prediction input does not match the model: {exc}",
        ) from exc

    return {
        "prediction": float(prediction),
    }


# ==================================================
# 8. Run application
# ==================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
