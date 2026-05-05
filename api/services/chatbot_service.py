import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

# Cargar variables de entorno
load_dotenv()

class PMOAssistant:
    def __init__(self):
        # Configuración de la base de datos
        db_path = os.path.join(os.getcwd(), "data", "pmo_rpa.db")
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # Inicialización del LLM (Claude 4.5 Haiku)
        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            temperature=0,
            max_tokens=1024,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Herramientas para el agente SQL
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # System Prompt estricto
        self.system_message = (
            "Eres un Asistente Director PMO experto en RPA. "
            "Tu base de datos tiene proyectos, fases, usuarios y roles. "
            "Debes responder a las preguntas de negocio construyendo y ejecutando consultas SQL seguras (solo lectura). "
            "Responde de manera profesional y resumida. "
            "IMPORTANTE: No realices operaciones de escritura (INSERT, UPDATE, DELETE, DROP)."
        )
        
        # Crear el agente
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type="tool-calling", # O "openai-tools" / "zero-shot-react-description" dependiendo de la versión
            prefix=self.system_message
        )

    def ask_bot(self, question: str) -> str:
        """
        Ejecuta la consulta del usuario a través del agente LangChain.
        """
        try:
            # En versiones recientes de LangChain se usa invoke
            response = self.agent_executor.invoke({"input": question})
            output = response.get("output", "No se pudo generar una respuesta.")
            
            # Hotfix: Flatten output if it's a list (Claude 4.5 returns content blocks)
            if isinstance(output, list):
                output = "".join([
                    item.get("text", "") if isinstance(item, dict) else str(item) 
                    for item in output
                ])
                
            return str(output)
        except Exception as e:
            return f"Error al procesar la consulta: {str(e)}"

# Instancia única para ser importada
assistant = None

def get_assistant():
    global assistant
    if assistant is None:
        assistant = PMOAssistant()
    return assistant
