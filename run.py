from app import create_app

app = create_app('development')

if __name__ == "__main__":
    print("🚀 Starting Parking App...")
    print("📍 Open your browser and go to: http://127.0.0.1:5000")
    app.run(debug = True , host = "0.0.0.0" , port = 5000)