"""
🦈 SharkClub Discord Bot - Reset de Usuários
Script para resetar APENAS os dados dos usuários antes do lançamento
Mantém a estrutura do banco intacta!
"""

import os
import sys

# Adiciona o diretório pai ao path para importar módulos do bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from database.connection import get_supabase

load_dotenv()

def reset_users_data():
    """
    Reseta APENAS os dados dos usuários:
    - Tabela users (XP, coins, streaks, níveis)
    - Tabela user_badges (insígnias conquistadas)
    - Tabela missions (progresso de missões)
    - Tabela user_minigame_cooldowns (cooldowns de minigames)
    - Tabela evaluations (avaliações)
    - Tabela call_requests (pedidos de call)
    - Tabela event_presence (presenças em eventos)
    
    NÃO TOCA em:
    - Estrutura das tabelas
    - Configurações do servidor
    - Definições de missões
    """
    
    supabase = get_supabase()
    
    if not supabase:
        print("❌ Erro: Não foi possível conectar ao Supabase")
        return False
    
    print("🦈 SharkClub - Reset de Usuários para Lançamento")
    print("=" * 50)
    print("\n⚠️  ATENÇÃO: Este script irá DELETAR todos os dados de usuários!")
    print("    Isso inclui: XP, moedas, streaks, insígnias, missões, etc.")
    print("\n    A estrutura do banco será mantida intacta.")
    
    confirmacao = input("\n🔐 Digite 'CONFIRMAR' para prosseguir: ")
    
    if confirmacao != "CONFIRMAR":
        print("\n❌ Operação cancelada.")
        return False
    
    print("\n🔄 Iniciando reset...")
    
    tabelas_para_limpar = [
        ("cooldowns", "Cooldowns"),
        ("rewards", "Recompensas"),
        ("missions", "Missões"),
        ("badges", "Insígnias"),
        ("evaluations", "Avaliações"),
        ("call_requests", "Pedidos de call"),
        ("event_presence", "Presenças em eventos"),
        ("activity_log", "Log de atividade"),
        ("notifications", "Notificações"),
        ("users", "Dados dos usuários"),
    ]
    
    for tabela, descricao in tabelas_para_limpar:
        try:
            # Deleta todos os registros da tabela
            result = supabase.table(tabela).delete().neq("id", 0).execute()
            print(f"   ✅ {descricao} ({tabela}) - Limpo!")
        except Exception as e:
            # Se a tabela não existir ou der erro, só avisa
            print(f"   ⚠️  {descricao} ({tabela}) - Aviso: {str(e)[:50]}")
    
    print("\n" + "=" * 50)
    print("🎉 Reset concluído com sucesso!")
    print("🦈 O bot está pronto para o lançamento!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    reset_users_data()
