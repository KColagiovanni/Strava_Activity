from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=5000  # Define the port to use when connecting.
    )