# app.py
# app.py
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})

   


@app.get("/api/hello")
def hello():
    return jsonify(message="Hello, world!")
    #return{
        
        #"Hello, World"
       # }
        
    



if __name__ == "__main__":
    # Ejecutar en desarrollo
    app.run(host="127.0.0.1", port=5000, debug=True)
