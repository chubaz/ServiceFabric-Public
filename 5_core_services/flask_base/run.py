from app import create_app

app = create_app()

if __name__ == "__main__":
    # Modalità debug solo per sviluppo locale senza Docker
    app.run(host="0.0.0.0", port=5000, debug=True)
