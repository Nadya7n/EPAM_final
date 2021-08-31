# EPAM_final
## Browser code executor

A web form for entering python code and executing it on the server side.

### Structure 
3 input fields:
1. Python code (mandatory field) 
2. Stdin (optional field)
3. Timeout, but less than 5 seconds (optional field)

When the program has finished - code, stdin, stdout and stderr will be displayed on our page. 

You can edit your code after execution and run it again.

### Important
For security reasons, we do not allow "os" module and functions "exec" and "eval". "open" is allowed with read-only permissions.

## Usage
### Docker
1. Download container image

    
    docker pull nadya7n/browser_code_executor:mytag

2. Run container

    
    docker run nadya7n/browser_code_executor:mytag

### Git
1. Download project

    
    git clone https://github.com/Nadya7n/EPAM_final.git

2. Install needed modules


    pip install -r requirements.txt

3. Run project


    python3 browser_code_executor/main.py

