### To setup this project in Linux environment 
Run these commands in Terminal:
* `git clone https://github.com/albertas/identity` # clones this repository  
* `cd identity`  # goes to project directory 
* `make`  # Prepares Python virtual env and installs dependencies to it
* `make test`  # Executes automated tests to see if everything was setup correctly
* `export REALID_API_KEY=...`  # Set API key in order to make API calls to RealID
* `make run`  # Starts local development server which can be accessed at localhost:8000
