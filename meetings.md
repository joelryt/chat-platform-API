# Meetings notes

## Meeting 1.
* **DATE: 3.2.2023
* **ASSISTANTS:** Mika

### Minutes
Quick overview of the project and it's scope

### Action points
Our team was adviced to make a more advanced graph of different data types and their relations




## Meeting 2.
* **DATE:** 20.2.2023
* **ASSISTANTS:** Ivan

### Minutes
Database models and their relations were discussed. Thoughts about how these relations will function within the API itself and what are their limitations

### Action points
ON DELETE relations should be specified also to the 'relationships' between classes. Meetings file should be filled and resource allocation should be slightly more spesific. Script should be made that automatically populates the database. Media URL and reaction type validity should be checked on either API or database side.




## Meeting 3.
* **DATE:** 10.3.2023
* **ASSISTANTS:** Mika

### Minutes
API documentation and implementation were discussed. Main points from the documentation was that the media and reactions could be put under messages in the URL tree and that the REST conformance discussion and explanation should be more thorough. The implementation was working fine and test coverage was fine (>90%). Notes on the implementation were that the current authentication method was more of a session token than API token, docstrings were missing from the resource methods and populate-db command needs the with_appcontext decorator to work with older flask versions.
### Action points
- Change URL for media and reactions to be under messages in the URL tree
- Make Rest conformance section in wiki more thorough, and tell how the addressability, uniform interface and statelessness is achieved in our API
- Add docstrings to resources and their methods
- Remove login and logout and use stateless API tokens for authentication
- Add with_appcontext decorator for populate-db command


## Meeting 4.
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Midterm meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




