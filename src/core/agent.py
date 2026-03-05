import google.generativeai as genai
import pandas as pd
import json
import plotly.express as px
import plotly.io as pio
from sqlalchemy import text
from src.core.config import get_settings
from src.core.database import get_db

class NashAgent:
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3.1-pro')

    def _get_schema_summary(self):
        """Returns the actual schema summary with SYSTEM_PROMPT embedded."""
        return """Eres NashAI, un agente de Inteligencia Artificial Neuro-Simbólica experto en bases de datos SQLite.

IDENTIDAD Y COMPORTAMIENTO (CRÍTICO): 
Eres un auditor algorítmico independiente creado por Daniel Narváez y Marcelo Villalobos. 
REGLA DE ORO: SOLO menciona tu nombre, tu identidad o tus creadores SI EL USUARIO TE LO PREGUNTA EXPLÍCITAMENTE (ej. "¿Quién eres?"). 
Para cualquier otra consulta sobre datos o análisis, RESPONDE DIRECTAMENTE. Cero saludos, cero introducciones, cero frases como "Como NashAI he analizado...". Ve directo al grano y entrega la información.

REGLAS ESTRICTAS:
1. Eres un sistema determinista. NO alucines tablas, columnas ni datos que no existan en el esquema proporcionado.
2. Devuelve ÚNICAMENTE el código SQL válido cuando se te pida analizar datos. No agregues explicaciones, ni saludos, ni comillas invertidas. Solo el código puro.
3. Todas las consultas deben ser de SOLO LECTURA (SELECT).
4. La llave principal para hacer JOIN entre las tablas es siempre 'numero_prestamo' (o 'numero_prestamo_vinculado').
5. Usa LOWER() y LIKE para búsquedas de texto flexibles.
6. Si piden 'mayores', 'peores' o 'top', usa ORDER BY y LIMIT 10 por defecto.

        Database Tables:
        1. dim_operaciones (columns: numero_prestamo, NOMBRE_OPERACION, PAIS, SECTOR_INSTITUCIONAL, MONTO_APROBADO)
        2. fact_indicadores_impacto (columns: numero_prestamo, nombre_metrica, valor_observado)
        3. fact_adjudicaciones (columns: numero_prestamo, IDENTIFICADOR_PROCESO, NOMBRE_ADQUISICION, NOMBRE_ADJUDICATARIO, PAIS_ADJUDICATARIO, monto_adjudicado_usd)
        4. fact_desembolsos (columns: numero_prestamo, anio, monto_desembolsado_usd)
        5. dim_transparencia_docs (columns: CODIGO_DOCUMENTO, TITULO_DOCUMENTO, TIPO_DOCUMENTAL, numero_prestamo_vinculado)
        6. dim_transparencia_solicitudes (columns: CODIGO_SOLICITUD, RESUMEN_SOLICITUD, ESTADO_SOLICITUD, numero_prestamo_vinculado)
        
        Relationships:
        - `numero_prestamo` in fact and dimension tables relates to `numero_prestamo` in `dim_operaciones`.
        - `numero_prestamo_vinculado` in transparencia tables relates to `numero_prestamo` in `dim_operaciones`.
        """

    def decide_intent(self, user_query: str, history: list = None) -> str:
        """Step 1: Intent Router"""
        recent_context = ""
        if history:
            recent_context = "Recent Conversation History:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])

        prompt = f"""
        {recent_context}
        
        User's Current Query: "{user_query}"
        
        Classify the intent into exactly one of these three categories:
        - "CHAT": A greeting, casual conversation, identity questions, or an abstract question that does NOT require querying the database.
        - "PLOT": An explicit request for a chart, graph, visualization, visual trend, or if the user says "grafica", "grafícame", "muéstrame un gráfico", "dibuja", "plot", "barras", "pastel", "líneas".
        - "DATA": A direct request for information, numbers, list of projects, or sums that requires querying the BCIE database tables, but DOES NOT explicitly ask for a visual chart or graph.
        
        Return ONLY the word CHAT, DATA, or PLOT. Nothing else.
        """
        try:
            response = self.model.generate_content(prompt)
            intent = response.text.strip().upper()
            if intent not in ["CHAT", "DATA", "PLOT"]:
                return "DATA" # Default if LLM hallucinates
            return intent
        except Exception:
            return "DATA"

    def chat_directly(self, user_query: str, history: list = None) -> str:
        """Step 2A: Direct natural conversation."""
        schema_and_identity = self._get_schema_summary()
        recent_context = ""
        if history:
            recent_context = "Recent Conversation Context:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])
            
        prompt = f"""
        {schema_and_identity}
        
        {recent_context}
        
        The user is talking to you causally or asking a generic question about your identity: "{user_query}"
        Respond naturally, politely, and proudly in Spanish according to your strict Identity guidelines. Be concise.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_sql(self, user_query: str, error_context: str = None, history: list = None) -> str:
        """Step 2B-1: SQL Generation"""
        schema_and_identity = self._get_schema_summary()
        recent_context = ""
        if history:
            recent_context = "Recent Conversation Context (Use for resolving pronouns or follow-up references):\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:]])
            
        prompt = f"""
        {schema_and_identity}
        
        Your ONLY job right now is to return a valid SQL SELECT query that answers the user's current question, taking into account the recent context if they are making a follow-up.
        
        {recent_context}
        
        User's Current Question: "{user_query}"
        
        {f"CRITICAL ERROR IN PREVIOUS ATTEMPT: {error_context}. FIX YOUR SQL." if error_context else ""}
        """
        response = self.model.generate_content(prompt)
        sql = response.text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def execute_sql(self, sql: str) -> pd.DataFrame:
        """Step 2B-2: Deterministic Data Retrieval"""
        db_gen = get_db()
        db = next(db_gen)
        try:
            result = db.execute(text(sql))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        finally:
            db.close()

    def generate_synthesis(self, user_query: str, df: pd.DataFrame) -> str:
        """Step 3: Analytical Contextualization (Read table -> Explain natural)"""
        schema_and_identity = self._get_schema_summary()
        # If df is too large, we just summarize first N rows to avoid huge prompt payloads
        head_str = df.head(50).to_markdown()
        row_count = len(df)
        
        prompt = f"""
        {schema_and_identity}
        
        The user asked: "{user_query}"
        
        I have executed a strict database query correctly. The resulting data table has {row_count} total rows.
        Here is a sample of the data:
        {head_str}
        
        Provide a natural, professional but conversational qualitative analysis in Spanish answering the user's question explicitly based purely on the data above. Do not hallucinate numbers not present in the table. Act strictly within your given identity and authorship. Be concise and insightful.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_plot(self, user_query: str, df: pd.DataFrame, error_context: str = None) -> dict:
        """Step 4: Generate Plotly Python Code"""
        head_str = df.head(10).to_markdown()
        schema = ', '.join(df.columns.tolist())
        
        prompt = f"""
        You are a Python plotting expert.
        The user wants a plot: "{user_query}"
        
        We have a pandas DataFrame `df` with columns: {schema}.
        Sample data:
        {head_str}
        
        {f"PREVIOUS ERROR: {error_context}. FIX YOUR CHART SCRIPT." if error_context else ""}
        
        Write Python code using `plotly.express` (as `px`) to generate a figure named `fig`.
        Rules:
        - Return ONLY the raw Python code. Do not use markdown blocks.
        - Do not show() the figure.
        - Assume `df` is already created and fully populated.
        - Use simple but aesthetic charts with titles.
        """
        code = self.model.generate_content(prompt).text.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        
        local_vars = {"df": df, "px": px}
        try:
            exec(code, globals(), local_vars)
            fig = local_vars.get("fig")
            if fig:
                return {
                    "success": True,
                    "code": code,
                    "fig": json.loads(fig.to_json())
                }
            return {"success": False, "error": "Code executed but `fig` object not defined."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process_query(self, user_query: str, history: list = None):
        """
        Main ReAct Neuro-Symbolic Flow
        """
        if history is None:
            history = []
            
        # Step 1: Decide Intent with History context
        intent = self.decide_intent(user_query, history)
        print(f"Detected Intent: {intent}")
        
        # Step 2A: Direct Chat
        if intent == "CHAT":
            natural_resp = self.chat_directly(user_query, history)
            return {
                "type": "chat",
                "text": natural_resp,
                "status": "success"
            }
        
        # Step 2B: Data/Plot execution (with SQL Self-Healing Loop)
        max_attempts = 4
        last_error = None
        sql = ""
        df = None
        
        for attempt in range(max_attempts):
            try:
                # Ask LLM for strictly SQL with history contextualization
                sql = self.generate_sql(user_query, error_context=last_error, history=history)
                # Mathematical deterministic execution
                df = self.execute_sql(sql)
                break  # Success, exit loop
                
            except Exception as e:
                # Capture and feedback error
                last_error = f"SQLite Error Output: {str(e)}"
                print(f"Attempt {attempt + 1}/{max_attempts} failed. Error: {last_error}")
                if attempt == max_attempts - 1:
                    return {
                        "type": "error",
                        "message": f"❌ Fallo al armar base de datos tras {max_attempts} reintentos. Error: {last_error}",
                        "sql": sql,
                        "status": "failed"
                    }
        
        # If we reached here, DB query was successful.
        if df is None:
             return {"type": "error", "message": "Failed to pull data without specific exception.", "status": "failed"}
             
        # Step 3: Analytical Synthesis
        synthesis = self.generate_synthesis(user_query, df)
        
        base_response = {
            "type": "data",
            "text": synthesis,  # Replacing generic success text with qualitative explanation
            "data": df.to_dict(orient="records"),
            "sql": sql,
            "status": "success"
        }
        
        # Step 4: Add Plot if needed
        if intent == "PLOT":
            plot_res = self.generate_plot(user_query, df)
            if plot_res["success"]:
                 base_response["type"] = "plot"
                 base_response["plot"] = plot_res["fig"]
                 base_response["code"] = plot_res["code"]
                 base_response["text"] = synthesis + "\n\nTambién he generado el gráfico solicitado correspondiente:"
            else:
                 # Inform we got the data but failed the graph
                 base_response["text"] += f"\n\n*(No pude generar la gráfica debido al siguiente error: {plot_res['error']})*"
                 
        return base_response
