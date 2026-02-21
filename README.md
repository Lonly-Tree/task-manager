# Task Manager

A command-line task manager with AI capabilities.

## Features

- **User Authentication:** Create an account and log in.
- **Task Management:** Add, delete, and mark tasks as done.
- **AI Functionality:** An "AI mode" that uses a `langchain` and `groq` to interact with the user.
- **Database:** Uses SQLAlchemy to store data.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Lonly-Tree/task-manager.git
   cd task-manager
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the environment variables:**
   Create a `.env` file in the root directory and add the following:
   ```
   TASKMGR_MASTER_KEY=your_master_key
   GROQ_MODEL_AI=your_groq_model_ai
   ```

## Usage

To run the application, execute the following command:
```bash
python main.py
```

## Project Structure
```
├───.gitignore
├───app.py
├───main.py
├───requirements.txt
├───__pycache__/
├───.git/
├───.venv/
│   ├───bin/
│   ├───include/
│   └───lib/
├───cli/
│   ├───__init__.py
│   ├───agent_commands.py
│   ├───auth_handler.py
│   ├───formatter.py
│   ├───note_handler.py
│   ├───router.py
│   ├───task_handler.py
│   └───__pycache__/
├───crypto/
│   ├───__init__.py
│   ├───crypto_service.py
│   ├───key_deriver.py
│   ├───key_manager.py
│   ├───password_hasher.py
│   └───__pycache__/
├───domain/
│   ├───__init__.py
│   ├───enums.py
│   ├───models.py
│   └───__pycache__/
├───INoteRepository/
│   ├───__init__.py
│   ├───note_repository.py
│   ├───task_repository.py
│   ├───user_repository.py
│   └───__pycache__/
├───repositories/
│   ├───__init__.py
│   ├───database.py
│   ├───interfaces.py
│   └───__pycache__/
├───services/
│   ├───__init__.py
│   ├───auth_service.py
│   ├───note_service.py
│   ├───session.py
│   ├───task_service.py
│   └───__pycache__/
└───tests/
```
