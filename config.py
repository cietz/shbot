"""
🦈 SharkClub Discord Bot - Configuration
Configurações centralizadas do sistema de gamificação
"""

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE NÍVEIS E XP - CARGOS
# Progressão de níveis com cargos temáticos
# ═══════════════════════════════════════════════════════════════

# XP necessário para cada nível
XP_PER_LEVEL = {
    1: 0,         # Náufrago (0-100 XP)
    2: 100,       # Pirata (100-300 XP)
    3: 300,       # Saqueador (300-500 XP)
    4: 500,       # Guardião do Tesouro (500-750 XP)
    5: 750,       # Caçador de Baleias (750-1250 XP)
    6: 1250,      # Tubarão Branco (1250-2000 XP)
    7: 2500,      # Rei do Oceano (2500-5000 XP)
    8: 5000,      # Deus dos Mares (5000-10000 XP)
    9: 10000,     # Lenda do Oceano (10000-17000 XP)
    10: 17000,    # MESTRE SUPREMO (17000-30000 XP)
}

# Nomes dos cargos por nível
CARGO_NAMES = {
    1: "Náufrago",
    2: "Pirata",
    3: "Saqueador",
    4: "Guardião do Tesouro",
    5: "Caçador de Baleias",
    6: "Tubarão Branco",
    7: "Rei do Oceano",
    8: "Deus dos Mares",
    9: "Lenda do Oceano",
    10: "MESTRE SUPREMO",
}

# Emojis dos cargos
CARGO_EMOJIS = {
    1: "🏴‍☠️🧭",
    2: "🏴‍☠️",
    3: "⚔️🏴‍☠️",
    4: "🔑🔱",
    5: "🐋🎣",
    6: "🦈",
    7: "👑🌊",
    8: "🔱⚡",
    9: "🌟",
    10: "💎👑",
}

# Nomes das insígnias por nível (com emoji)
BADGE_NAMES = {
    1: "🏴‍☠️ Náufrago",
    2: "🏴‍☠️ Pirata",
    3: "⚔️ Saqueador",
    4: "🔑 Guardião do Tesouro",
    5: "🐋 Caçador de Baleias",
    6: "🦈 Tubarão Branco",
    7: "👑 Rei do Oceano",
    8: "🔱 Deus dos Mares",
    9: "🌟 Lenda do Oceano",
    10: "💎 MESTRE SUPREMO",
}

# Descrições dos cargos
BADGE_DESCRIPTIONS = {
    1: "Acabou de chegar ao oceano",
    2: "Começando sua jornada pirata",
    3: "Saqueando os mares do marketing",
    4: "Protegendo tesouros valiosos",
    5: "Caçando as grandes oportunidades",
    6: "Predador temido dos mares",
    7: "Dominando o oceano do tráfego",
    8: "Poder divino sobre os mares",
    9: "Lenda viva do oceano",
    10: "Domínio absoluto - O Mestre Supremo",
}

# IDs dos cargos no Discord (configure com os IDs reais do seu servidor)
# Deixe None se quiser que o bot crie os cargos automaticamente
DISCORD_ROLE_IDS = {
    1: None,  # ID do cargo Náufrago
    2: None,  # ID do cargo Pirata
    3: None,  # ID do cargo Saqueador
    4: None,  # ID do cargo Guardião do Tesouro
    5: None,  # ID do cargo Caçador de Baleias
    6: None,  # ID do cargo Tubarão Branco
    7: None,  # ID do cargo Rei do Oceano
    8: None,  # ID do cargo Deus dos Mares
    9: None,  # ID do cargo Lenda do Oceano
    10: None, # ID do cargo MESTRE SUPREMO
}

# ═══════════════════════════════════════════════════════════════
# IDs DOS CANAIS FIXOS
# ═══════════════════════════════════════════════════════════════

CHANNEL_IDS = {
    "ranking": 1457725911591031001,
    "checkin": 1454626025416953988,
    "missoes": 1457725913650298979,
    "minigames": 1457725915319636093,
    "ajudou": 1457735753080504565,
    "calls_marcadas": 1458442547939508235,
    "loja": 1459267133904126188,
}

# Cores dos cargos (em hexadecimal)
CARGO_COLORS = {
    1: 0x808080,   # Cinza - Náufrago
    2: 0x8B4513,   # Marrom - Pirata
    3: 0xCD7F32,   # Bronze - Saqueador
    4: 0xC0C0C0,   # Prata - Guardião
    5: 0x4169E1,   # Azul Royal - Caçador
    6: 0x00CED1,   # Turquesa - Tubarão Branco
    7: 0xFFD700,   # Dourado - Rei do Oceano
    8: 0x9400D3,   # Roxo - Deus dos Mares
    9: 0xFF4500,   # Laranja - Lenda
    10: 0xFF0000,  # Vermelho - Mestre Supremo
}

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE CHECK-IN E STREAK
# ═══════════════════════════════════════════════════════════════

CHECKIN_BASE_XP = 50           # XP base do check-in
CHECKIN_STREAK_BONUS = 10      # XP adicional por dia de streak
CHECKIN_MAX_XP = 200           # XP máximo do check-in
STREAK_RESET_HOURS = 72        # Horas para resetar streak (72h = 3 dias)
CHECKIN_COOLDOWN_HOURS = 20    # Cooldown mínimo entre check-ins

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE MISSÕES
# ═══════════════════════════════════════════════════════════════

# Missões Diárias
DAILY_MISSION_XP_RANGE = (100, 250)
DAILY_MISSIONS_COUNT = 4  # Número de missões diárias disponíveis

# Missões Semanais
WEEKLY_MISSION_XP_RANGE = (200, 400)

# Missões Secretas
SECRET_MISSION_XP_RANGE = (700, 1000)

# Missões Secretas (Apenas VIPs)
SECRET_MISSIONS = {
    "secreta_1": {
        "emoji": "⭐",
        "name": "Secreta 1 - Atividade Consistente",
        "description": "Atividade real por 5 dias consecutivos (chat, call ou post)",
        "objective": "5 dias consecutivos de atividade",
        "target": 5,  # 5 dias consecutivos
        "xp_reward": 50,
        "coins_reward": 0,
        "type": "secret",
        "category": "activity",
        "vip_only": True,
    },
    "secreta_2": {
        "emoji": "⭐",
        "name": "Secreta 2 - Mentor da Comunidade",
        "description": "Ajudar 3 membros diferentes na semana (dúvidas, feedbacks ou insights)",
        "objective": "Ajudar 3 membros diferentes",
        "target": 3,  # 3 membros diferentes
        "xp_reward": 50,
        "coins_reward": 0,
        "type": "secret",
        "category": "help",
        "vip_only": True,
    },
}

# ═══════════════════════════════════════════════════════════════
# MINI-GAMES - ROLETA DE TUBARÕES (SLOTS)
# Prêmios: XP (10-200) 60%, Booster 2x 35%, Insígnia+5coins 4%, Moeda servidor 1%
# ═══════════════════════════════════════════════════════════════

ROULETTE_COOLDOWN_HOURS = 24  # 1 giro por dia (mais giros podem ser ganhos em eventos)

# Símbolos da roleta (tubarões) - ordem de raridade
SHARK_SLOTS = [
    {"emoji": "🐟", "name": "Peixinho", "weight": 30},      # Comum
    {"emoji": "🐠", "name": "Peixe Tropical", "weight": 25}, # Comum
    {"emoji": "🐡", "name": "Baiacu", "weight": 20},         # Incomum
    {"emoji": "🦈", "name": "Tubarão", "weight": 15},        # Raro
    {"emoji": "🐋", "name": "Baleia", "weight": 7},          # Muito Raro
    {"emoji": "🦑", "name": "Kraken", "weight": 3},          # Lendário
]

# Prêmios da ROLETA baseados nas probabilidades pedidas
ROULETTE_PRIZES = [
    # XP (10-200) - 60%
    {"name": "XP Pequeno", "type": "xp", "xp": 10, "weight": 15, "emoji": "✨"},
    {"name": "XP Médio", "type": "xp", "xp": 50, "weight": 20, "emoji": "💫"},
    {"name": "XP Grande", "type": "xp", "xp": 100, "weight": 15, "emoji": "⭐"},
    {"name": "XP Mega", "type": "xp", "xp": 200, "weight": 10, "emoji": "🌟"},
    # Booster 2x por 1h - 35%
    {"name": "Booster 2x XP (1h)", "type": "booster", "booster": 2.0, "booster_duration": 3600, "weight": 35, "emoji": "🚀"},
    # Insígnia rara + 5 SHARK COINS - 4%
    {"name": "Insígnia Rara + 5 Coins!", "type": "badge_coins", "badge": "lucky_shark", "coins": 5, "weight": 4, "emoji": "🏅"},
    # Moeda do servidor (SHARK COIN rara) - 1%
    {"name": "💎 SHARK COIN RARA!", "type": "rare_coin", "coins": 10, "weight": 1, "emoji": "💎"},
]

# Prêmios por resultado dos SLOTS (baseado em quantos iguais)
SLOTS_PRIZES = {
    # 3 iguais = JACKPOT
    "jackpot": {
        "🐟🐟🐟": {"xp": 50, "coins": 5, "name": "Trio de Peixinhos"},
        "🐠🐠🐠": {"xp": 80, "coins": 5, "name": "Trio Tropical"},
        "🐡🐡🐡": {"xp": 120, "coins": 10, "name": "Trio Baiacu"},
        "🦈🦈🦈": {"xp": 250, "coins": 20, "name": "SHARK JACKPOT!", "booster": 2.0, "booster_duration": 3600},
        "🐋🐋🐋": {"xp": 400, "coins": 50, "name": "MEGA BALEIA!", "booster": 2.0, "booster_duration": 3600, "secret_mission": True},
        "🦑🦑🦑": {"xp": 800, "coins": 100, "name": "🔥 KRAKEN LENDÁRIO! 🔥", "badge": "kraken_master", "booster": 2.5, "booster_duration": 7200, "secret_mission": True},
    },
    # 2 iguais = Prêmio menor
    "pair": {"xp": 25, "coins": 2, "name": "Par!"},
    # Nenhum igual = Perdeu
    "lose": {"xp": 5, "coins": 0, "name": "Tente novamente..."},
}

# GIFs para cada símbolo do slot (tubarões e peixes animados)
SLOT_SYMBOL_GIFS = {
    "🐟": "https://media1.tenor.com/m/ug1RBqTLNroAAAAC/fish-swimming.gif",
    "🐠": "https://media1.tenor.com/m/5jtSjLiMx0oAAAAC/tropical-fish.gif",
    "🐡": "https://media1.tenor.com/m/qw7rBLnNiecAAAAC/puffer-fish.gif",
    "🦈": "https://media1.tenor.com/m/PDVFVhVPd8kAAAAC/shark-jaws.gif",
    "🐋": "https://media1.tenor.com/m/T-oP4WSHjLoAAAAC/whale-ocean.gif",
    "🦑": "https://media1.tenor.com/m/6R1RCM4TP-QAAAAC/squid-ocean.gif",
}

# GIFs especiais para resultados
SLOT_RESULT_GIFS = {
    "jackpot": "https://media1.tenor.com/m/v8hVDs0LSIoAAAAd/shark-attack.gif",
    "shark_jackpot": "https://media1.tenor.com/m/PDVFVhVPd8kAAAAC/shark-jaws.gif",
    "pair": "https://media1.tenor.com/m/YGJp_7M-LfIAAAAC/fish-school.gif",
    "lose": "https://media1.tenor.com/m/HK-Z_LqhbfgAAAAC/sad-fish.gif",
}

# ═══════════════════════════════════════════════════════════════
# MINI-GAMES - LOOTBOX (CAIXA MISTERIOSA)
# Ganha ao: 7 dias login, participar call, finalizar missão semanal
# ═══════════════════════════════════════════════════════════════

# Prêmios da LOOTBOX com probabilidades
LOOTBOX_PRIZES = [
    # XP grande (100-500) - 85%
    {"name": "XP Grande", "type": "xp", "xp_min": 100, "xp_max": 500, "weight": 85, "emoji": "⭐"},
    # 5 SHARK COINS - 8%
    {"name": "5 SHARK COINS", "type": "coins", "coins": 5, "weight": 8, "emoji": "🪙"},
    # CARGO REI DA RASPADINHA + CALL PV - 6%
    {"name": "👑 REI DA RASPADINHA!", "type": "special_role", "role": "rei_raspadinha", "weight": 6, "emoji": "👑"},
    # Insígnias temáticas - 1%
    {"name": "Insígnia Lendária", "type": "legendary_badge", "badge": "lootbox_legend", "weight": 1, "emoji": "🏆"},
]

# Chance de pular 1 nível na lootbox (separado)
LOOTBOX_SKIP_LEVEL_CHANCE = 2  # 2% de chance

# ═══════════════════════════════════════════════════════════════
# MINI-GAMES - RASPADINHA SHARK
# Premiação rápida, barata, viciante igual app chinês
# ═══════════════════════════════════════════════════════════════

SCRATCH_COOLDOWN_DAYS = 7  # 1 ticket por semana

SCRATCH_PRIZES = [
    {"name": "😢 Perdedor", "xp": 5, "weight": 40, "emoji": "😢"},
    {"name": "🎫 Pequeno Prêmio", "xp": 30, "weight": 35, "emoji": "🎫"},
    {"name": "🎟️ Prêmio Médio", "xp": 80, "weight": 15, "emoji": "🎟️"},
    {"name": "🏆 Prêmio Grande!", "xp": 150, "weight": 8, "emoji": "🏆"},
    {"name": "🦈 JACKPOT MEGALODON!", "xp": 500, "weight": 2, "emoji": "🦈", "special_badge": "megalodon_jackpot"},
]

# GIF da raspadinha
SCRATCH_GIF = "https://media1.tenor.com/m/EJFHxAxO-bQAAAAC/scratch-card.gif"

# ═══════════════════════════════════════════════════════════════
# CORES E ESTILO
# ═══════════════════════════════════════════════════════════════

EMBED_COLOR_PRIMARY = 0x0099FF    # Azul shark
EMBED_COLOR_SUCCESS = 0x00FF88    # Verde sucesso
EMBED_COLOR_WARNING = 0xFFAA00    # Laranja aviso
EMBED_COLOR_ERROR = 0xFF4444      # Vermelho erro
EMBED_COLOR_GOLD = 0xFFD700       # Dourado conquista
EMBED_COLOR_LEGENDARY = 0x9B59B6  # Roxo lendário

# Emojis do sistema
EMOJI_SHARK = "🦈"
EMOJI_XP = "⭐"
EMOJI_LEVEL = "📊"
EMOJI_STREAK = "🔥"
EMOJI_COINS = "🪙"
EMOJI_BADGE = "🏅"
EMOJI_MISSION = "📋"
EMOJI_CHECKIN = "✅"

# ═══════════════════════════════════════════════════════════════
# ANTI-SPAM E MODERAÇÃO
# ═══════════════════════════════════════════════════════════════

MESSAGE_XP_COOLDOWN = 60         # Segundos entre mensagens que dão XP
MESSAGE_XP_AMOUNT = 5            # XP por mensagem válida
VOICE_XP_INTERVAL = 300          # Segundos para ganhar XP em call (5 min)
VOICE_XP_AMOUNT = 15             # XP por intervalo em call
MIN_MESSAGE_LENGTH = 10          # Caracteres mínimos para ganhar XP

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE MONITORAMENTO DE ATIVIDADE
# ═══════════════════════════════════════════════════════════════

# IDs dos canais que serão monitorados para atividade (posts/comentários)
# Adicione os IDs dos canais específicos que você quer monitorar
MONITORED_CHANNELS = []  # Ex: [123456789012345678, 987654321098765432]

# XP por atividade nos canais monitorados
MONITORED_POST_XP = 25           # XP por post em canal monitorado
MONITORED_COMMENT_XP = 10        # XP por comentário em canal monitorado
MONITORED_COOLDOWN = 120         # Segundos entre XP em canais monitorados

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE AVALIAÇÃO COM ESTRELAS E COMENTÁRIOS
# Avaliações públicas com 1-5 estrelas e comentários visíveis
# ═══════════════════════════════════════════════════════════════

# Cooldown entre avaliações do mesmo par (em horas)
EVALUATION_COOLDOWN_HOURS = 24

# Sistema de estrelas (1-5)
EVALUATION_STARS = {
    1: {"emoji": "⭐", "label": "Ruim", "xp": 10, "color": 0xFF4444},
    2: {"emoji": "⭐⭐", "label": "Regular", "xp": 25, "color": 0xFFAA00},
    3: {"emoji": "⭐⭐⭐", "label": "Bom", "xp": 50, "color": 0xFFFF00},
    4: {"emoji": "⭐⭐⭐⭐", "label": "Muito Bom", "xp": 75, "color": 0x88FF00},
    5: {"emoji": "⭐⭐⭐⭐⭐", "label": "Excelente", "xp": 100, "color": 0x00FF88},
}

# Configurações do comentário
EVALUATION_COMMENT_MAX_LENGTH = 200  # Máximo de caracteres do comentário
EVALUATION_COMMENT_MIN_LENGTH = 10   # Mínimo de caracteres do comentário

# XP bônus para quem avalia (incentivo a avaliar)
EVALUATOR_XP_BONUS = 10  # XP ganho por fazer uma avaliação

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE MISSÕES SEMANAIS
# Missões recorrentes que aparecem toda semana
# ═══════════════════════════════════════════════════════════════

# Missões Semanais Principais
WEEKLY_MISSIONS = {
    "cacada_semana": {
        "emoji": "🏆",
        "name": "Caçada da Semana",
        "description": "Participar de pelo menos 2 calls nervosas",
        "objective": "Participar de 2 calls nervosas",
        "target": 2,
        "xp_reward": 100,
        "coins_reward": 10,
        "type": "weekly",
        "category": "calls",
    },
    "mentor_fantasma": {
        "emoji": "🎯",
        "name": "Mentor Fantasma",
        "description": "Ajudar 2 membros em dúvidas nos canais de marketing",
        "objective": "Ajudar 2 membros com dúvidas",
        "target": 2,
        "xp_reward": 100,
        "coins_reward": 10,
        "type": "weekly",
        "category": "help",
    },
    "fire_funil": {
        "emoji": "🔥",
        "name": "Fire de Funil",
        "description": "Criar 1 post de valor real no canal de conteúdo",
        "objective": "Criar 1 post de valor",
        "target": 1,
        "xp_reward": 100,
        "coins_reward": 10,
        "type": "weekly",
        "category": "content",
    },
    "cacador_tendencias": {
        "emoji": "📈",
        "name": "Caçador de Tendências",
        "description": "Postar 1 insight atual sobre tráfego, criativo, copy ou métricas",
        "objective": "Postar 1 insight de tendência",
        "target": 1,
        "xp_reward": 100,
        "coins_reward": 10,
        "type": "weekly",
        "category": "trends",
    },
    "sharkmind": {
        "emoji": "🧠",
        "name": "SharkMind",
        "description": "Responder corretamente 5 perguntas de um quiz semanal",
        "objective": "Acertar 5 perguntas do quiz",
        "target": 5,
        "xp_reward": 100,
        "coins_reward": 10,
        "type": "weekly",
        "category": "quiz",
    },
}

# Missões Diárias Recorrentes
DAILY_MISSIONS_TEMPLATES = {
    "daily_checkin": {
        "emoji": "✅",
        "name": "Check-in Diário",
        "description": "Fazer seu check-in diário",
        "objective": "Fazer check-in",
        "target": 1,
        "xp_reward": 25,
        "coins_reward": 5,
    },
    "daily_messages": {
        "emoji": "💬",
        "name": "Conversa do Dia",
        "description": "Enviar mensagens no servidor",
        "objective": "Enviar 10 mensagens",
        "target": 10,
        "xp_reward": 30,
        "coins_reward": 5,
    },
    "daily_react": {
        "emoji": "👍",
        "name": "Reações Positivas",
        "description": "Reagir a mensagens de outros membros",
        "objective": "Reagir a 5 mensagens",
        "target": 5,
        "xp_reward": 20,
        "coins_reward": 3,
    },
    "daily_help": {
        "emoji": "🤝",
        "name": "Mão Amiga",
        "description": "Ajudar um membro com uma dúvida",
        "objective": "Ajudar 1 membro",
        "target": 1,
        "xp_reward": 40,
        "coins_reward": 8,
    },
}

# Quantidade de missões diárias para sortear
DAILY_MISSIONS_COUNT = 3           # FREE: 3 missões
VIP_DAILY_MISSIONS_EXTRA = 1       # VIP: +1 missão extra

# Horário de reset das missões diárias (BRT)
MISSIONS_RESET_HOUR = 0            # Meia-noite

# ═══════════════════════════════════════════════════════════════
# SISTEMA VIP - CONFIGURAÇÃO COMPLETA
# Diferenciação entre contas FREE e VIP
# ═══════════════════════════════════════════════════════════════

# Cores e Emojis
EMBED_COLOR_VIP = 0xFFD700          # Dourado VIP
EMOJI_VIP = "👑"
EMOJI_FREE = "🎫"
EMOJI_FASTPASS = "⚡"
EMOJI_EVENT = "🎪"

# Status do VIP (para exibição)
VIP_STATUS = {
    "free": {"name": "Free", "emoji": "🎫", "color": 0x808080},
    "vip": {"name": "VIP", "emoji": "👑", "color": 0xFFD700},
}

# ═══════════════════════════════════════════════════════════════
# 1. SISTEMA DE LOGIN DIÁRIO
# ═══════════════════════════════════════════════════════════════

# XP do Check-in
FREE_CHECKIN_XP = 50                 # XP base para FREE
VIP_CHECKIN_XP = 100                 # XP base para VIP (bônus)

# Cooldowns de Check-in
FREE_CHECKIN_COOLDOWN_HOURS = 20     # FREE: 20h entre check-ins
VIP_CHECKIN_COOLDOWN_HOURS = 16      # VIP: 16h entre check-ins

# ═══════════════════════════════════════════════════════════════
# 2. SISTEMA DE TEMPO ONLINE
# ═══════════════════════════════════════════════════════════════

# Tempo necessário para ganhar recompensa (em minutos)
FREE_DAILY_ONLINE_MINUTES = 60       # FREE: 60 min online/dia
VIP_DAILY_ONLINE_MINUTES = 30        # VIP: 30 min online/dia (FastPass)

# XP por completar tempo online diário
ONLINE_TIME_REWARD_XP = 75           # XP ao completar tempo online
ONLINE_TIME_REWARD_COINS = 10        # Moedas ao completar tempo online

# Intervalo para contabilizar tempo online (em segundos)
ONLINE_TIME_CHECK_INTERVAL = 60      # Checa a cada 60 segundos

# ═══════════════════════════════════════════════════════════════
# 3. SISTEMA DE INTERAÇÃO NO CHAT
# ═══════════════════════════════════════════════════════════════

# Mensagens necessárias por dia
FREE_DAILY_MESSAGES = 10             # FREE: 10 mensagens/dia obrigatórias
VIP_DAILY_MESSAGES = 0               # VIP: Não precisa (FastPass)

# XP por completar interação diária
CHAT_INTERACTION_REWARD_XP = 50      # XP ao completar interações
CHAT_INTERACTION_REWARD_COINS = 5    # Moedas ao completar interações

# Configurações de mensagem válida
MIN_MESSAGE_CHARS = 5                # Mínimo de caracteres para contar
MESSAGE_COOLDOWN_SECONDS = 30        # Cooldown entre mensagens contadas

# ═══════════════════════════════════════════════════════════════
# 4. SISTEMA DE EVENTOS E LIVES
# ═══════════════════════════════════════════════════════════════

# Multiplicador de presença em eventos
FREE_EVENT_PRESENCE_MULTIPLIER = 1   # FREE: 1x presença
VIP_EVENT_PRESENCE_MULTIPLIER = 2    # VIP: 2x presença

# XP por presença em evento
EVENT_PRESENCE_BASE_XP = 100         # XP base por evento
EVENT_PRESENCE_BASE_COINS = 20       # Moedas base por evento

# ═══════════════════════════════════════════════════════════════
# 5. SISTEMA DE FASTPASS (VIP)
# ═══════════════════════════════════════════════════════════════

# FastPass permite VIPs pularem requisitos
FASTPASS_ENABLED = True              # FastPass ativo
FASTPASS_SKIPS_ONLINE_TIME = True    # Pula tempo online
FASTPASS_SKIPS_CHAT_INTERACTION = True  # Pula interação no chat
FASTPASS_XP_BONUS = 1.5              # Bônus de XP do FastPass

# ═══════════════════════════════════════════════════════════════
# 6. SISTEMA DE STREAKS E RECOMPENSAS PROGRESSIVAS
# ═══════════════════════════════════════════════════════════════

# Marcos de Streak
STREAK_MILESTONES = {
    7: {
        "name": "🔥 Semana de Fogo",
        "xp": 500,
        "coins": 50,
        "badge": "🔥 7 Dias",
        "description": "7 dias consecutivos de login!",
        "lootbox": True,  # Ganha caixa misteriosa
    },
    14: {
        "name": "⚡ Duas Semanas Imparável",
        "xp": 1200,
        "coins": 150,
        "badge": "⚡ 14 Dias",
        "description": "14 dias consecutivos de login!",
        "lootbox": True,
        "booster": {"multiplier": 2.0, "duration_hours": 24},  # Booster 2x por 24h
    },
    30: {
        "name": "🦈 TUBARÃO FRENÉTICO",
        "xp": 3000,
        "coins": 500,
        "badge": "🦈 Tubarão Frenético",
        "description": "30 dias consecutivos! Você é um verdadeiro predador!",
        "lootbox": True,
        "booster": {"multiplier": 2.5, "duration_hours": 48},  # Booster 2.5x por 48h
        "special": True,  # Recompensa especial
    },
}

# Bônus de XP por dia de streak (cumulativo)
STREAK_XP_BONUS_PER_DAY = 10         # +10 XP por dia de streak

# Dias para resetar streak
STREAK_RESET_HOURS = 48              # Reseta após 48h sem login

# ═══════════════════════════════════════════════════════════════
# 7. BENEFÍCIOS VIP GERAIS
# ═══════════════════════════════════════════════════════════════

VIP_XP_MULTIPLIER = 1.5              # VIPs ganham 50% mais XP
VIP_COINS_MULTIPLIER = 2.0           # VIPs ganham o dobro de moedas

# Cooldowns para VIPs (em horas) - Reduzidos
VIP_ROULETTE_COOLDOWN_HOURS = 20     # Free: 24h, VIP: 20h
VIP_SCRATCH_COOLDOWN_DAYS = 2        # Free: 3 dias, VIP: 2 dias

# Recursos exclusivos VIP
VIP_EXTRA_DAILY_MISSIONS = 1         # +1 missão diária extra
VIP_LOOTBOX_BONUS_CHANCE = 10        # +10% chance de prêmio raro
VIP_PROFILE_BADGE = "👑 VIP"         # Badge exclusiva no perfil

# ═══════════════════════════════════════════════════════════════
# LISTA DE BENEFÍCIOS (para exibição)
# ═══════════════════════════════════════════════════════════════

FREE_REQUIREMENTS = [
    f"📋 Login diário obrigatório",
    f"⏰ {FREE_DAILY_ONLINE_MINUTES} minutos online/dia",
    f"💬 {FREE_DAILY_MESSAGES} mensagens/dia no chat",
    f"🎪 Presença simples em eventos",
]

VIP_BENEFITS = [
    f"{EMOJI_VIP} Login diário com bônus ({VIP_CHECKIN_XP} XP)",
    f"{EMOJI_FASTPASS} FastPass: Menos tempo online ({VIP_DAILY_ONLINE_MINUTES} min)",
    f"{EMOJI_FASTPASS} FastPass: Sem obrigação de chat",
    f"🎪 Presença X2 em eventos e lives",
    f"⭐ Multiplicador de XP permanente ({VIP_XP_MULTIPLIER}x)",
    f"🪙 Dobro de moedas em todas as atividades",
    f"⏰ Cooldowns reduzidos",
    f"🏅 Badge exclusiva {VIP_PROFILE_BADGE}",
]

# ═══════════════════════════════════════════════════════════════
# INSÍGNIAS ESPECIAIS DE STREAK
# ═══════════════════════════════════════════════════════════════

STREAK_BADGES = {
    "7_dias": {"emoji": "🔥", "name": "7 Dias de Fogo", "rarity": "common"},
    "14_dias": {"emoji": "⚡", "name": "14 Dias Imparável", "rarity": "rare"},
    "30_dias": {"emoji": "🦈", "name": "Tubarão Frenético", "rarity": "legendary"},
}

# ═══════════════════════════════════════════════════════════════
# SISTEMA DE LOJA (SHOP)
# Itens compráveis com SHARK COINS
# ═══════════════════════════════════════════════════════════════

EMOJI_SHOP = "🛒"
EMOJI_CALL = "📞"

# Itens da loja
SHOP_ITEMS = {
    "call_expert": {
        "id": "call_expert",
        "emoji": "📞",
        "name": "Call com Expert",
        "description": "Solicite uma call privada com qualquer membro do servidor",
        "price_free": 1000,      # Preço para usuários FREE
        "price_vip": 800,        # Preço para usuários VIP (20% desconto)
        "category": "services",
        "requires_target": True,  # Requer escolher um membro
    },
}

# Status de pedidos de call
CALL_STATUS = {
    "pending": {"emoji": "⏳", "name": "Pendente", "color": 0xFFAA00},
    "accepted": {"emoji": "✅", "name": "Aceito", "color": 0x00FF88},
    "scheduled": {"emoji": "📅", "name": "Agendado", "color": 0x00AAFF},
    "declined": {"emoji": "❌", "name": "Recusado", "color": 0xFF4444},
    "expired": {"emoji": "⌛", "name": "Expirado", "color": 0x808080},
}

# Tempo limite para resposta do expert (em horas)
CALL_REQUEST_EXPIRY_HOURS = 48
