from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Verifica se a chave está sendo lida corretamente
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY não encontrada. Verifique seu arquivo .env")

# Inicialização do cliente OpenAI
client = OpenAI(api_key=api_key)

# Sistema de contexto para o assistente
SYSTEM_CONTEXT = """Você é um assistente virtual especializado em finanças pessoais, 
focado em ajudar pessoas a gerenciar melhor seu dinheiro. Forneça respostas claras, 
objetivas e práticas, baseadas em princípios sólidos de educação financeira. 
Evite dar conselhos sobre investimentos específicos."""

class FinanceAssistant:
    def __init__(self):
        self.conversation_history = {}
    
    def get_conversation_history(self, user_id):
        """Recupera ou cria histórico de conversa para um usuário"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        return self.conversation_history[user_id]
    
    def generate_response(self, user_id, user_message):
        """Gera uma resposta usando a API da OpenAI"""
        try:
            conversation = self.get_conversation_history(user_id)
            
            # Preparar mensagens para a API
            messages = [
                {"role": "system", "content": SYSTEM_CONTEXT}
            ]
            
            # Adicionar histórico de conversa
            for msg in conversation[-5:]:  # Limitando a 5 mensagens anteriores
                messages.append(msg)
                
            # Adicionar mensagem atual do usuário
            messages.append({"role": "user", "content": user_message})
            
            # Fazer chamada à API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Mudamos para GPT-3.5-turbo
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extrair resposta
            assistant_response = response.choices[0].message.content
            
            # Atualizar histórico
            self.conversation_history[user_id].append({"role": "user", "content": user_message})
            self.conversation_history[user_id].append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."

# Instanciar o assistente
finance_assistant = FinanceAssistant()

@app.route('/')
def home():
    """Rota para a página inicial"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Endpoint para processar perguntas do usuário"""
    try:
        data = request.json
        user_message = data.get('message')
        user_id = data.get('user_id', 'default_user')  # Identificador único do usuário
        
        if not user_message:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        # Gerar resposta
        response = finance_assistant.generate_response(user_id, user_message)
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /ask: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True)