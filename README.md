# PWP SPRING 2023
# Chat Platform API
# Group information
* Student 1. Jere Kinnunen Jere.Kinnunen@oulu.fi
* Student 2. Lauri Klemettilä Lauri.Klemettila@student.oulu.fi
* Student 3. Joonas Tuutijärvi Joonas.Tuutijarvi@oulu.fi
* Student 4. Joel Rytkönen Joel.Rytkonen@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

# Requirements
Install the required python packages from requirements.txt:
```
pip install -r requirements.txt
```

# Database
SQLite database is used (at least for the development phase).
SQLAlchemy is used to create the database.<br>
To initialize the database, run the init-db command:
```
flask --app src/app init-db
```
To populate the database with some data after initializing it, run the populate-db command:
```
flask --app src/app populate-db
```
To test the creation of instances of all database models, run the db_test file with pytest.
```
pytest .\src\db_test.py
```
