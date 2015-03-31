## System Description ##

1) A hardware company hosts the backend authentication service (`main.py`) and SQL database on a secure webserver. As a demonstration, it is being hosted live at `https://eecs588-auth.herokuapp.com/`.  
2) The web browser plugin sends a unique device ID, one-time password, authentication token, and remote URL to the service.  
3) The service authenticates the device using the UID and OTP, or fails.  
4) Device trust level is retrieved from the database and is sent to the remote URL along with the client's autentication token. This authenticates the client to the remote service.

## File: main.py ##

- Purpose  
 - Runs an authentication server for a device company.  
 - Clients can send a POST request to /authenticate in order to verify their identity with a remote server.  
 - The company can send a POST request to /register in order to register a new device in the database. This service is unauthenticated and solely for testing purposes.  
- Requirements  
 - Standard Python installation  
 - Flask (web microframework)  
 - psycopg2 (PostgreSQL database API)  
 - A database server running PostgreSQL.  
- Usage  
 - Run `python main.py`  
 - Expects PORT and DATABASE_URL environment variables.  

## File: utility.py ##

- Purpose  
 - Emulate the browser plug-in for testing and allow a company to register new devices in the database.
- Requirements  
 - Standard Python installation  
- Usage  
 - Run `python utility.py [local|remote] [register|authenticate] deviceID`  
 - local | remote: connect to a locally-hosted or remote authentication server (URLs are found in `utility.py`)
 - register | authenticate: send a request to register a new device as the company, or authenticate a device as the browser plug-in
 - deviceID: the unique ID of the device to register or authenticate
