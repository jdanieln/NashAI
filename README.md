# NashAI

NashAI is a "Neuro-Symbolic" AI agent for the Central American Bank for Economic Integration (BCIE). It allows users to ask natural language questions about financial open data.

## Research Paper / Citation

This work is described in our research paper. If you use NashAI in your research or project, please cite it using the following DOI:

[![DOI](https://img.shields.io/badge/DOI-10.13140%2FRG.2.2.19081.51047-blue)](https://doi.org/10.13140/RG.2.2.19081.51047)
**(DOI: [10.13140/RG.2.2.19081.51047](https://doi.org/10.13140/RG.2.2.19081.51047))**

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

3.  **Data**:
    The raw CSV data and the initialized SQLite database (`data/nash_finance.db`) are already included in this repository. You do not need to run the ETL process manually unless you want to update the data. *(If needed, run `python src/utils/etl.py` to recreate the database from the CSV files in `data/raw/`).*

4.  **Run Backend**:
    Start the FastAPI server.
    ```bash
    uvicorn src.main:app --reload
    ```

5.  **Run Frontend**:
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
