# OrderFood Website
This is a repository for OrderFood Website made using [Flask](https://www.palletsprojects.com/p/flask/). Users can order foods by logging into their account.

## Installation
1. Install [Python 3](https://www.python.org/) in your system. Make sure that `pip` is available for installing Python packages.
2. Install [`virtualenv`](https://virtualenv.pypa.io/en/latest/) for creating Python Virtual Environments.
    ```bash
    pip install virtualenv
    ```
3. Clone this repository or Extract it into a specific folder and `cd` into it.
    ```bash
    cd OrderFood-website
    ```
4. Create vitual environment called `env` using `virtualenv`.
    - Linux  or Mac
        ```bash
        virtualenv env
        source env/bin/activate
        ```
    - Windows
        ```
        virtualenv env
        env\Scripts\activate
        ```
    You can use the `deactivate` command for deactivating the virtual environment.
5. Install the required Python packages by the command:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. You have to **edit and provide own config values** in the [config_sample.py](orderfood/config_sample.py) file and **rename the file** as `config.py`. **Otherwise you cannot run the server** in the next step.
2. You can initialize(create) the required Database from Python shell using the command provided in [db_initialization.txt](db_initialization.txt).
3. You can start the Flask app server by calling
   ```bash
   python3 run.py
   ```
4. The website can be accessed through a browser at [127.0.0.1:5000](http://127.0.0.1:5000/) or [localhost:5000](localhost:5000)

## Issues 
If you find any bugs/issues or want to request for new feature, please raise an issue.