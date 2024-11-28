from flask import Flask, jsonify

app = Flask(__name__)

# Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return jsonify({"status": "success", "message": "API is running!"})

if __name__ == '__main__':
    app.run(debug=True)