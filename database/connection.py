"""
🦈 SharkClub Discord Bot - Supabase Connection
Gerenciamento de conexão com Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Retorna instância do cliente Supabase (singleton)"""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env"
            )
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client


async def init_database():
    """
    Inicializa o banco de dados.
    As tabelas devem ser criadas no Supabase Dashboard ou via migrations.
    Esta função apenas verifica a conexão.
    """
    try:
        client = get_supabase()
        # Testa a conexão fazendo uma query simples
        result = client.table('users').select('user_id').limit(1).execute()
        print("✅ Conexão com Supabase estabelecida!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        print("📝 Certifique-se de criar as tabelas no Supabase Dashboard.")
        return False


# ═══════════════════════════════════════════════════════════════
# SQL PARA CRIAR TABELAS NO SUPABASE
# Execute este SQL no SQL Editor do Supabase Dashboard
# ═══════════════════════════════════════════════════════════════

SUPABASE_SETUP_SQL = """
-- ═══════════════════════════════════════════════════════════════
-- 🦈 SHARKCLUB DISCORD BOT - SCHEMA COMPLETO
-- Execute este SQL no SQL Editor do Supabase Dashboard
-- Última atualização: Dezembro 2024
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- TABELA PRINCIPAL: USERS
-- Armazena todos os dados dos usuários
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS users (
    -- Identificação
    user_id BIGINT PRIMARY KEY,           -- ID do Discord
    username TEXT,                         -- Nome de exibição
    
    -- Sistema de Progressão
    xp INTEGER DEFAULT 0,                  -- Experiência total
    level INTEGER DEFAULT 1,               -- Nível atual (1-10)
    
    -- Sistema de Check-in/Streak
    current_streak INTEGER DEFAULT 0,      -- Streak atual (dias consecutivos)
    longest_streak INTEGER DEFAULT 0,      -- Maior streak alcançado
    last_checkin TIMESTAMPTZ,              -- Data/hora do último check-in
    
    -- Economia
    coins INTEGER DEFAULT 0,               -- Moedas do servidor
    
    -- Boosters Temporários
    xp_multiplier REAL DEFAULT 1.0,        -- Multiplicador de XP ativo
    multiplier_expires_at TIMESTAMPTZ,     -- Quando o booster expira
    
    -- Sistema VIP
    is_vip BOOLEAN DEFAULT FALSE,          -- Se é VIP (padrão: FREE)
    vip_expires_at TIMESTAMPTZ,            -- Quando VIP expira (NULL = permanente)
    
    -- Metadados
    created_at TIMESTAMPTZ DEFAULT NOW(),  -- Data de criação
    updated_at TIMESTAMPTZ DEFAULT NOW()   -- Última atualização
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: BADGES (Insígnias)
-- Insígnias e conquistas dos usuários
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS badges (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    badge_name TEXT NOT NULL,              -- Nome/emoji da insígnia
    badge_type TEXT DEFAULT 'permanent',   -- Tipo: permanent, admin, event, etc
    earned_at TIMESTAMPTZ DEFAULT NOW(),   -- Quando foi conquistada
    is_temporary BOOLEAN DEFAULT FALSE,    -- Se é temporária
    expires_at TIMESTAMPTZ,                -- Quando expira (se temporária)
    UNIQUE(user_id, badge_name)
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: MISSIONS (Missões)
-- Sistema de missões diárias, semanais e secretas
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    mission_id TEXT NOT NULL,              -- ID único da missão
    mission_type TEXT NOT NULL,            -- Tipo: daily, weekly, secret
    status TEXT DEFAULT 'active',          -- Status: active, completed, expired
    progress INTEGER DEFAULT 0,            -- Progresso atual
    target INTEGER DEFAULT 1,              -- Meta a atingir
    xp_reward INTEGER DEFAULT 0,           -- XP de recompensa
    started_at TIMESTAMPTZ DEFAULT NOW(),  -- Quando iniciou
    completed_at TIMESTAMPTZ,              -- Quando completou
    expires_at TIMESTAMPTZ                 -- Quando expira
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: REWARDS (Recompensas)
-- Caixas, tickets e outras recompensas acumuláveis
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rewards (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    reward_type TEXT NOT NULL,             -- Tipo: mystery_box, scratch_ticket, etc
    available_count INTEGER DEFAULT 0,     -- Quantidade disponível
    last_used TIMESTAMPTZ,                 -- Último uso
    UNIQUE(user_id, reward_type)
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: COOLDOWNS
-- Controle de cooldowns por usuário/ação
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cooldowns (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,             -- Tipo: checkin, roulette, scratch, etc
    last_used TIMESTAMPTZ DEFAULT NOW(),   -- Última execução
    UNIQUE(user_id, action_type)
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: RANKINGS
-- Rankings semanais e mensais
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rankings (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    weekly_xp INTEGER DEFAULT 0,           -- XP ganho na semana
    monthly_xp INTEGER DEFAULT 0,          -- XP ganho no mês
    collaboration_score INTEGER DEFAULT 0,  -- Score de colaboração
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: ACTIVITY_LOG
-- Log de atividades em canais monitorados
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,               -- ID do usuário
    channel_id BIGINT NOT NULL,            -- ID do canal
    activity_type TEXT NOT NULL,           -- Tipo: post, comment, reaction
    message_id BIGINT,                     -- ID da mensagem (opcional)
    created_at TIMESTAMPTZ DEFAULT NOW()   -- Quando ocorreu
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: EVALUATIONS
-- Avaliações de membros por admins
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS evaluations (
    id SERIAL PRIMARY KEY,
    evaluator_id BIGINT NOT NULL,          -- ID de quem avaliou
    target_id BIGINT NOT NULL,             -- ID de quem foi avaliado
    evaluation_type TEXT NOT NULL,         -- Tipo: participativo, prestativo, etc
    comment TEXT,                          -- Comentário opcional
    xp_given INTEGER DEFAULT 0,            -- XP dado na avaliação
    created_at TIMESTAMPTZ DEFAULT NOW()   -- Quando foi avaliado
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: DAILY_PROGRESS
-- Progresso diário do usuário (tempo online, mensagens, etc)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS daily_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,  -- Data do progresso
    
    -- Tempo Online (em minutos)
    online_minutes INTEGER DEFAULT 0,         -- Minutos online acumulados
    online_completed BOOLEAN DEFAULT FALSE,   -- Se completou o requisito
    online_reward_claimed BOOLEAN DEFAULT FALSE, -- Se já recebeu recompensa
    
    -- Mensagens no Chat
    messages_count INTEGER DEFAULT 0,         -- Mensagens enviadas
    chat_completed BOOLEAN DEFAULT FALSE,     -- Se completou o requisito
    chat_reward_claimed BOOLEAN DEFAULT FALSE, -- Se já recebeu recompensa
    
    -- Login Diário
    checkin_done BOOLEAN DEFAULT FALSE,       -- Se fez check-in
    
    -- Metadados
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, date)
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: EVENTS
-- Eventos e Lives do servidor
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_name TEXT NOT NULL,                 -- Nome do evento
    event_type TEXT DEFAULT 'live',           -- Tipo: live, event, workshop
    description TEXT,                         -- Descrição do evento
    xp_reward INTEGER DEFAULT 100,            -- XP base de recompensa
    coins_reward INTEGER DEFAULT 20,          -- Moedas base de recompensa
    starts_at TIMESTAMPTZ,                    -- Início do evento
    ends_at TIMESTAMPTZ,                      -- Fim do evento
    is_active BOOLEAN DEFAULT TRUE,           -- Se está ativo
    created_by BIGINT,                        -- ID do criador
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- TABELA: EVENT_PRESENCE
-- Presenças marcadas em eventos
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS event_presence (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    presence_multiplier INTEGER DEFAULT 1,    -- Multiplicador (VIP = 2x)
    xp_earned INTEGER DEFAULT 0,              -- XP ganho
    coins_earned INTEGER DEFAULT 0,           -- Moedas ganhas
    marked_at TIMESTAMPTZ DEFAULT NOW(),      -- Quando marcou presença
    
    UNIQUE(event_id, user_id)
);

-- ═══════════════════════════════════════════════════════════════
-- ÍNDICES PARA PERFORMANCE
-- ═══════════════════════════════════════════════════════════════

-- Users
CREATE INDEX IF NOT EXISTS idx_users_xp ON users(xp DESC);
CREATE INDEX IF NOT EXISTS idx_users_level ON users(level DESC);
CREATE INDEX IF NOT EXISTS idx_users_vip ON users(is_vip) WHERE is_vip = TRUE;

-- Badges
CREATE INDEX IF NOT EXISTS idx_badges_user ON badges(user_id);

-- Missions
CREATE INDEX IF NOT EXISTS idx_missions_user ON missions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_missions_type ON missions(mission_type, status);

-- Rankings
CREATE INDEX IF NOT EXISTS idx_rankings_weekly ON rankings(weekly_xp DESC);
CREATE INDEX IF NOT EXISTS idx_rankings_monthly ON rankings(monthly_xp DESC);

-- Activity Log
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_channel ON activity_log(channel_id, created_at DESC);

-- Evaluations
CREATE INDEX IF NOT EXISTS idx_evaluations_target ON evaluations(target_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluations_evaluator ON evaluations(evaluator_id, created_at DESC);

-- Daily Progress
CREATE INDEX IF NOT EXISTS idx_daily_progress_user ON daily_progress(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_progress_date ON daily_progress(date);

-- Events
CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active, starts_at);
CREATE INDEX IF NOT EXISTS idx_event_presence_event ON event_presence(event_id);
CREATE INDEX IF NOT EXISTS idx_event_presence_user ON event_presence(user_id, marked_at DESC);

-- ═══════════════════════════════════════════════════════════════
-- FUNÇÃO E TRIGGER: AUTO-UPDATE updated_at
-- ═══════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════
-- MIGRAÇÃO: ADICIONAR COLUNAS VIP (para bancos existentes)
-- Execute apenas se já tiver a tabela users criada anteriormente
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_vip BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS vip_expires_at TIMESTAMPTZ;

-- ═══════════════════════════════════════════════════════════════
-- RLS (Row Level Security) - OPCIONAL
-- Descomente as linhas abaixo se quiser habilitar RLS
-- ═══════════════════════════════════════════════════════════════

-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE badges ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE missions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rewards ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE cooldowns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rankings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════════════════
-- FIM DO SCHEMA 🦈
-- ═══════════════════════════════════════════════════════════════
"""

