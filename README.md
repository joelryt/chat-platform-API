# PWP SPRING 2023
# Chat Platform API
# Group information
* Student 1. Jere Kinnunen Jere.Kinnunen@oulu.fi
* Student 2. Lauri Klemettilä Lauri.Klemettila@student.oulu.fi
* Student 3. Joonas Tuutijärvi Joonas.Tuutijarvi@oulu.fi
* Student 4. Joel Rytkönen Joel.Rytkonen@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

# Project setup
Install the project and required packages running the following command from project root folder:
```
pip install -e .
```
the -e option installs the project in editable mode (recommended for development work).

# Database
SQLite database is used (at least for the development phase).
SQLAlchemy is used to create the database.<br>
To initialize the database, run the init-db command:
```
flask --app src\app init-db
```
To populate the database with some data after initializing it, run the populate-db command:
```
flask --app src\app populate-db
```

# Deploying the API
Deploy the API locally:
```
flask --app src\app run
```

# API Documentation
Api documentation can be found from path <code>/apidocs/</code> when the app is running.

# Running the tests
Running the tests require pytest package. Install pytest package using pip:
```
pip install pytest
```
To run all the tests, use command:
```
pytest tests
```
To include coverage report, install the pytest-cov package and run the tests with --cov option:
```
pip install pytest-cov
```
```
pytest tests --cov
```

# Client application
You can try out the API functionality with this small client application.
Make sure that you have initialized and populated the database beforehand,
so that there is something for the client to show.
```
python client_app.py
```
