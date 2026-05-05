import sys
import os

# Añadir el directorio raíz al path para poder importar la API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.chatbot_service import get_assistant
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Verificar API KEY
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: La variable de entorno ANTHROPIC_API_KEY no está configurada.")
        print("Por favor, agrégala al archivo .env")
        return

    print("🤖 Iniciando Cerebro del Asistente PMO (Anthropic Haiku)...")
    try:
        assistant = get_assistant()
        print("✅ Conexión establecida con la base de datos y LLM.")
        print("-" * 50)
        print("Escribe tu pregunta para el PMO Assistant (o 'salir' para terminar):")
        
        while True:
            user_input = input("\n👤 Usuario: ")
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego!")
                break
            
            if not user_input.strip():
                continue

            print("🧠 Pensando...")
            respuesta = assistant.ask_bot(user_input)
            
            print(f"\n🤖 Assistant: {respuesta}")
            print("-" * 30)

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
