
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ SUPABASE_URL ou SUPABASE_KEY não encontrados no .env")
    exit(1)

supabase: Client = create_client(url, key)

print("🔄 Tentando adicionar coluna is_admin na tabela users...")

# Tentativa de executar SQL via RPC se disponível, ou insert/select para debug
# Infelizmente a lib client não tem DDL direto.
# Vou tentar usar o workaround de chamar uma query SQL se houver uma função RPC configurada,
# mas provavelmente não tem.

# Se não der para alterar via código (limitação da client lib),
# o usuário terá que adicionar manualmente no dashboard do Supabase.
# Mas vamos tentar um truque: alguns clientes permitem rodar query crua se tiver permissão.

try:
    # Verifica se a coluna existe pegando um usuário
    response = supabase.table('users').select('is_admin').limit(1).execute()
    print("✅ Coluna 'is_admin' já existe!")
except Exception as e:
    print(f"⚠️ Erro ao verificar coluna (esperado se não existir): {e}")
    # A lib python do supabase não suporta DDL (ALTER TABLE) diretamente.
    print("\n🛑 ATENÇÃO: A biblioteca Python do Supabase não permite alterar estrutura de tabelas.")
    print("Você precisa ir no SQL Editor do Supabase e rodar:")
    print("\nALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
    
    # Workaround: Se tivermos uma funcão exec_sql no supabase (comum em setups avançados), podemos tentar:
    try:
        response = supabase.rpc('exec_sql', {'query': 'ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'}).execute()
        print("✅ Coluna criada via RPC!")
    except:
        pass
