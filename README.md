# NashAI

NashAI is a "Neuro-Symbolic" AI agent for the Central American Bank for Economic Integration (BCIE). It allows users to ask natural language questions about financial open data.

## Features

- **Natural Language Interface**: Ask questions in plain Spanish or English.
- **SQL Generation**: Automatically converts questions into SQL queries for data retrieval.
- **Data Visualization**: Generates Plotly charts when requested.
- **Self-Correction**: If a generated query fails, the agent attempts to fix it automatically.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.
    ```bash
    cp .env.example .env
    ```

3.  **Data Preparation**:
    Place the following CSV files in `data/raw/`:
    - `activities-web.csv`
    - `procesos_competitivos.csv`
    - `adjudicatarios_psd.csv`

4.  **Run ETL**:
    Initialize the database by running the ETL script.
    ```bash
    python src/utils/etl.py
    ```

5.  **Run Backend**:
    Start the FastAPI server.
    ```bash
    uvicorn src.main:app --reload
    ```

6.  **Run Frontend**:
    In a separate terminal, start the Streamlit app.
    ```bash
    streamlit run src/ui.py
    ```

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: SQLite
- **AI**: Gemini 1.5 Pro via `google-generativeai`
- **Data**: Pandas, Plotly
