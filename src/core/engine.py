import pandas as pd
import google.generativeai as genai
import plotly.express as px
import plotly.io as pio
import traceback
import json
import re
from sqlalchemy import text
from src.core.config import get_settings
from src.core.database import get_db

class NashNeuralEngine:
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def _get_schema_summary(self):
        """Returns a simplified schema summary for the LLM."""
        # Hardcoding known schema based on ETL or querying DB if needed.
        # For this scaffold, we provide a descriptive context.
        return """
        Database Tables:
        1. proyectos (columns: Activity Name, Sector, Status, Amount)
        2. licitaciones (columns: Process Name, Description, Deadline, Amount)
        3. adjudicaciones (columns: Contractor, Project, Amount, Date)
        """

    def decide_intent(self, user_query: str) -> str:
        """Step 1: Decide if we need SQL (data) or Python (plot)."""
        prompt = f"""
        User Query: "{user_query}"
        
        Classify the intent into one of:
        - "SQL": if the user asks for data retrieval, list, filtered items, or simple numbers.
        - "PLOT": if the user asks for a chart, graph, visualization, or trend.
        
        Return ONLY the word SQL or PLOT.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().upper()
        except Exception:
            return "SQL" # Default fall back

    def generate_sql(self, user_query: str, error_context: str = None) -> str:
        """Step 2a: Generate SQL Query."""
        schema = self._get_schema_summary()
        prompt = f"""
        You are a SQLite expert. 
        Schema: {schema}
        
        User Query: "{user_query}"
        
        {f"Previous Error: {error_context}. Fix the SQL." if error_context else ""}
        
        Return ONLY the raw SQL query. Do not use markdown blocks like ```sql.
        Ensure the SQL is valid for SQLite.
        """
        response = self.model.generate_content(prompt)
        sql = response.text.strip()
        # Cleanup
        sql = sql.replace("```sql", "").replace("```", "")
        return sql

    def generate_plot_code(self, df_head: str, user_query: str, error_context: str = None) -> str:
        """Step 2b: Generate Python Plotly Code."""
        prompt = f"""
        You are a Python Data Visualization expert using Plotly Express.
        We have a pandas DataFrame `df` with the following first 5 rows:
        {df_head}
        
        User Query: "{user_query}"
        
        {f"Previous Error: {error_context}. Fix the code." if error_context else ""}
        
        Write Python code to generate a plotly figure named `fig`.
        Return ONLY the valid python code. Do not use markdown blocks.
        Assume `df` is already correct.
        Use `px` (plotly.express).
        Do not show the figure (don't call fig.show()), just create `fig`.
        """
        response = self.model.generate_content(prompt)
        code = response.text.strip()
        code = code.replace("```python", "").replace("```", "")
        return code

    def execute_sql(self, sql: str) -> pd.DataFrame:
        """Step 3a: Execute SQL."""
        # Using a fresh connection for the query
        db_gen = get_db()
        db = next(db_gen)
        try:
            # SQLAlchemy text() is required for raw sql
            result = db.execute(text(sql))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        finally:
            db.close() # Ensure connection is closed

    def process_query(self, user_query: str):
        """Main Neuro-Symbolic Loop."""
        intent = self.decide_intent(user_query)
        
        if intent == "SQL":
            retries = 2
            last_error = None
            for attempt in range(retries + 1):
                try:
                    sql = self.generate_sql(user_query, error_context=last_error)
                    df = self.execute_sql(sql)
                    return {
                        "type": "data",
                        "data": df.to_dict(orient="records"),
                        "sql": sql,
                        "text": f"Found {len(df)} results."
                    }
                except Exception as e:
                    last_error = str(e)
                    continue
            return {"type": "error", "message": f"Failed to execute SQL after retries. Error: {last_error}"}
            
        elif intent == "PLOT":
            # For plotting, we usually need data first. 
            # In a full system, we might ask for SQL then Plot. 
            # Here, assuming we query all relevant data or specific table for simplicity
            # Or asking LLM to get data first.
            
            # Simple approach: Get data via SQL first (auto-generated) -> Then Plot
            sql_retries = 2
            sql_error = None
            df = None
            
            # Sub-step: Get Data
            for attempt in range(sql_retries + 1):
                try:
                    # Modify query to imply fetching data for plotting
                    sql = self.generate_sql(f"Get data to plot: {user_query}", error_context=sql_error)
                    df = self.execute_sql(sql)
                    if not df.empty:
                        break
                except Exception as e:
                    sql_error = str(e)
            
            if df is None or df.empty:
                return {"type": "error", "message": "Could not retrieve data for plotting."}

            # Sub-step: Generate Plot
            plot_retries = 2
            plot_error = None
            for attempt in range(plot_retries + 1):
                try:
                    code = self.generate_plot_code(str(df.head()), user_query, error_context=plot_error)
                    local_vars = {"df": df, "px": px}
                    exec(code, {}, local_vars)
                    fig = local_vars.get("fig")
                    if fig:
                        return {
                            "type": "plot",
                            "plot_json": json.dumps(fig, cls=pio.utils.PlotlyJSONEncoder),
                            "code": code,
                            "text": "Here is the visualization."
                        }
                except Exception as e:
                    plot_error = str(e)
            
            return {"type": "error", "message": f"Failed to generate plot. Error: {plot_error}"}

        return {"type": "unknown", "message": "Could not understand intent."}
