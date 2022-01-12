from app import app
import os
from flask_cors import CORS  

CORS(app)

port = int(os.environ.get('PORT', 5000))
app.run(host = '0.0.0.0', port = port)
