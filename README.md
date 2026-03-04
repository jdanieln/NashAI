# NashAI

NashAI es un agente de Inteligencia Artificial "Neuro-Simbólico" diseñado para el Banco Centroamericano de Integración Económica (BCIE). Su propósito principal es permitir a los usuarios consultar datos financieros abiertos utilizando lenguaje natural de forma intuitiva y efectiva.

El núcleo de NashAI radica en su arquitectura **Neuro-Simbólica**: combina la capacidad de comprensión del lenguaje natural de los Grandes Modelos de Lenguaje (LLMs) (la parte *neuronal*, impulsada por Gemini) con la precisión y determinismo de las consultas estructuradas en bases de datos (la parte *simbólica*, utilizando SQL). 

## Publicación y Citación (DOI)

Este trabajo ha sido detallado exhaustivamente en nuestra publicación científica. Si utilizas NashAI en tu investigación o proyecto, por favor cítalo utilizando el siguiente DOI:

[![DOI](https://img.shields.io/badge/DOI-10.13140%2FRG.2.2.19081.51047-blue)](https://doi.org/10.13140/RG.2.2.19081.51047)
**(DOI: [10.13140/RG.2.2.19081.51047](https://doi.org/10.13140/RG.2.2.19081.51047))**

## Características Principales

- **Interfaz en Lenguaje Natural**: Pemite realizar consultas complejas sobre datos financieros escribiendo de manera conversacional, ya sea en Español o Inglés.
- **Generación de SQL (Text-to-SQL)**: Convierte automáticamente las preguntas del usuario en consultas SQL precisas para extraer solo los datos necesarios.
- **Visualización de Datos Dinámica**: Genera gráficos interactivos utilizando Plotly cuando la consulta del usuario lo amerita o lo solicita explícitamente.
- **Auto-Corrección (Self-Healing)**: Si una consulta SQL generada contiene errores o falla en tiempo de ejecución, el agente recupera el error de la base de datos e intenta corregir su propia consulta automáticamente.

## Estructura del Proyecto

El repositorio está organizado separando claramente la extracción de datos, el núcleo lógico del agente, la API del backend y la interfaz gráfica del usuario (frontend).

```text
NashvilleAI/
├── data/
│   ├── raw/                  # Contiene los archivos CSV originales descargados.
│   └── nash_finance.db       # Base de datos SQLite inicializada y lista para usar.
├── notebooks/                
│   └── NashAI_ETL.ipynb      # Notebook interactivo para pruebas y exploración del proceso ETL.
├── src/
│   ├── core/                 # Lógica de negocio y el "Cerebro" de NashAI
│   │   ├── agent.py          # Definición del Agente Neuro-Simbólico (Generación SQL, Corrección, Gráficos).
│   │   ├── config.py         # Configuraciones globales y variables de entorno.
│   │   └── database.py       # Conexión y ejecución de consultas en la base de datos SQLite.
│   ├── utils/
│   │   └── etl.py            # Script encargado del proceso ETL (Extracción, Transformación y Carga de CSV a DB).
│   ├── main.py               # Punto de entrada del Backend (API REST usando FastAPI).
│   └── ui.py                 # Interfaz gráfica de usuario construida con Streamlit.
├── .env.example              # Plantilla para las variables de entorno necesarias.
├── requirements.txt          # Dependencias de Python necesarias para correr el proyecto.
└── README.md                 # Archivo de documentación (este archivo).
```

## Configuración y Ejecución

1. **Instalar Dependencias**:
   Asegúrate de tener un entorno virtual activo y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```

2. **Variables de Entorno**:
   Copia el archivo de ejemplo para crear tu propio archivo `.env` en la raíz del proyecto.
   ```bash
   cp .env.example .env
   ```
   Abre el archivo `.env` resultante e inserta tu clave de API de Gemini (`GEMINI_API_KEY`).

3. **Datos y Base de Datos**:
   Los archivos de datos en bruto (CSV) ubicados en `data/raw/` y la base de datos resultante (`data/nash_finance.db`) **ya están incluidos en este repositorio**. 
   Al descargarlo, ya estás listo para iniciar el sistema sin pasos adicionales sobre los datos.
   *(Nota: Opcionalmente, si cambias los CSV originales o necesitas reconstruir la base de datos desde cero, puedes ejecutar el proceso ETL corriendo `python src/utils/etl.py`).*

4. **Ejecutar el Backend (FastAPI)**:
   Abre una terminal interactiva y levanta el servidor que albergará la lógica de la API de NashAI.
   ```bash
   uvicorn src.main:app --reload
   ```

5. **Ejecutar el Frontend (Streamlit)**:
   En **otra ventana** de tu terminal, levanta la interfaz gráfica donde interactuarás con el agente.
   ```bash
   streamlit run src/ui.py
   ```
   *La aplicación debería abrirse automáticamente en tu navegador web en la dirección `http://localhost:8501/`.*

## Tecnologías Utilizadas

- **Backend / API**: FastAPI (Python)
- **Frontend / Interfaz Gráfica**: Streamlit
- **Base de Datos**: SQLite nativo
- **Inteligencia Artificial**: Google Gemini 1.5 Pro (vía `google-generativeai`)
- **Manipulación de Datos y Gráficos**: Pandas y Plotly
