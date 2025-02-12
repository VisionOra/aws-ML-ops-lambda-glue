from mangum import Mangum
from main import app  # adjust this import if your FastAPI app is defined in a different module

handler = Mangum(app)
