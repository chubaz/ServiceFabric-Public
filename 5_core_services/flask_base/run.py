from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=not app.config['IS_PRODUCTION'] and app.config['ENABLE_DEBUG_ROUTES'])
