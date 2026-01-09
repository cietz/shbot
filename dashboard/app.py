from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sys
import logging
from functools import wraps
from dotenv import load_dotenv

# Adiciona diretório pai ao path para importar modulos do bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_supabase

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Dashboard")

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "shark_secret_key_123")  # Trocar em produção

# Configurações
ADMIN_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash("Senha incorreta!", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    supabase = get_supabase()
    
    # Busca estatísticas
    total_users = supabase.table('users').select('*', count='exact').execute().count
    
    # Para somar XP e Coins, precisamos fazer fetch all (Supabase JS client tem sum(), python client é mais limitado para aggregation direto sem RPC)
    # Para performance em produção, usaríamos RPC no postgres. Para agora, um fetch simples.
    # Limitando a 1000 para não estourar em demo
    users_data = supabase.table('users').select('xp,coins').limit(1000).execute().data
    
    total_xp = sum(u['xp'] for u in users_data)
    total_coins = sum(u['coins'] for u in users_data)
    
    active_missions = supabase.table('missions').select('*', count='exact').eq('status', 'active').execute().count
    
    # Top Users
    top_users = supabase.table('users').select('*').order('xp', desc=True).limit(5).execute().data
    
    stats = {
        'total_users': total_users,
        'total_xp': total_xp,
        'total_coins': total_coins,
        'active_missions': active_missions
    }
    
    return render_template('home.html', stats=stats, top_users=top_users, title="Dashboard Overview", active_page='home')

@app.route('/users')
@login_required
def users():
    search = request.args.get('q')
    supabase = get_supabase()
    
    query = supabase.table('users').select('*').order('xp', desc=True)
    
    if search:
        # Tenta buscar por ID se for número
        if search.isdigit():
            query = query.eq('user_id', int(search))
        else:
            query = query.ilike('username', f'%{search}%')
            
    users = query.limit(50).execute().data
    
    return render_template('users.html', users=users, title="Gerenciar Usuários", active_page='users', search_query=search or '')

@app.route('/users/update', methods=['POST'])
@login_required
def update_user():
    try:
        user_id = int(request.form.get('user_id'))  # Convert to int for BIGINT column
        xp = int(request.form.get('xp'))
        coins = int(request.form.get('coins'))
        is_vip = request.form.get('is_vip') == 'true'
        
        logger.info(f"Updating user {user_id}: xp={xp}, coins={coins}, is_vip={is_vip}")
        
        supabase = get_supabase()
        result = supabase.table('users').update({
            'xp': xp,
            'coins': coins,
            'is_vip': is_vip
        }).eq('user_id', user_id).execute()
        
        logger.info(f"Update result: {result}")
        
        flash(f"Usuário {user_id} atualizado com sucesso!", "success")
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        flash(f"Erro ao atualizar: {str(e)}", "error")
        
    return redirect(url_for('users'))

@app.route('/missions')
@login_required
def missions():
    supabase = get_supabase()
    
    # Filters
    filter_status = request.args.get('status')
    filter_type = request.args.get('type')
    filter_user = request.args.get('user')
    
    query = supabase.table('missions').select('*').order('started_at', desc=True)
    
    if filter_status:
        query = query.eq('status', filter_status)
    if filter_type:
        query = query.eq('mission_type', filter_type)
    if filter_user and filter_user.isdigit():
        query = query.eq('user_id', int(filter_user))
    
    missions_data = query.limit(100).execute().data
    
    # Get all users for name lookup
    users_data = supabase.table('users').select('user_id,username').execute().data
    user_map = {u['user_id']: u['username'] or f"User {u['user_id']}" for u in users_data}
    
    # Add username to each mission
    for mission in missions_data:
        mission['username'] = user_map.get(mission['user_id'], f"ID: {mission['user_id']}")
    
    # Get unique users that have missions (for dropdown)
    all_missions = supabase.table('missions').select('user_id').execute().data
    unique_user_ids = list(set(m['user_id'] for m in all_missions))
    users_with_missions = [
        {'user_id': uid, 'username': user_map.get(uid, f"ID: {uid}")}
        for uid in unique_user_ids
    ]
    users_with_missions.sort(key=lambda x: x['username'].lower())
    
    # Stats
    stats = {
        'active': len([m for m in all_missions if m.get('status') == 'active']),
        'completed': len([m for m in all_missions if m.get('status') == 'completed']),
        'weekly': len([m for m in all_missions if m.get('mission_type') == 'weekly' and m.get('status') == 'active'])
    }
    
    return render_template('missions.html', 
                           missions=missions_data, 
                           stats=stats,
                           users_with_missions=users_with_missions,
                           filter_status=filter_status or '',
                           filter_type=filter_type or '',
                           filter_user=filter_user or '',
                           title="Gerenciar Missões", 
                           active_page='missions')

@app.route('/missions/advance', methods=['POST'])
@login_required
def advance_mission():
    try:
        mission_id = int(request.form.get('mission_id'))
        
        supabase = get_supabase()
        
        # Get current mission
        mission = supabase.table('missions').select('*').eq('id', mission_id).single().execute().data
        
        if mission and mission['status'] == 'active':
            new_progress = mission['progress'] + 1
            
            if new_progress >= mission['target']:
                # Complete mission
                supabase.table('missions').update({
                    'progress': new_progress,
                    'status': 'completed',
                    'completed_at': 'now()'
                }).eq('id', mission_id).execute()
                flash(f"Missão #{mission_id} completada!", "success")
            else:
                # Just advance
                supabase.table('missions').update({
                    'progress': new_progress
                }).eq('id', mission_id).execute()
                flash(f"Missão #{mission_id} avançada para {new_progress}/{mission['target']}", "success")
        else:
            flash("Missão não encontrada ou já completada", "error")
            
    except Exception as e:
        logger.error(f"Error advancing mission: {e}")
        flash(f"Erro: {str(e)}", "error")
    
    return redirect(url_for('missions'))

@app.route('/missions/complete', methods=['POST'])
@login_required
def complete_mission():
    try:
        mission_id = int(request.form.get('mission_id'))
        user_id = int(request.form.get('user_id'))
        mission_name = request.form.get('mission_name')
        mission_type = request.form.get('mission_type')
        
        supabase = get_supabase()
        
        # Get mission data
        mission = supabase.table('missions').select('*').eq('id', mission_id).single().execute().data
        
        if mission and mission['status'] == 'active':
            # Complete the mission
            supabase.table('missions').update({
                'progress': mission['target'],
                'status': 'completed'
            }).eq('id', mission_id).execute()
            
            # Give rewards (default values if not configured)
            xp_reward = 100
            coins_reward = 10
            mission_display_name = mission_name
            
            # Try to get rewards from config
            try:
                import config
                if mission_type == 'weekly' and mission_name in config.WEEKLY_MISSIONS:
                    xp_reward = config.WEEKLY_MISSIONS[mission_name].get('xp_reward', 100)
                    coins_reward = config.WEEKLY_MISSIONS[mission_name].get('coins_reward', 10)
                    mission_display_name = config.WEEKLY_MISSIONS[mission_name].get('name', mission_name)
                elif mission_type == 'daily' and mission_name in config.DAILY_MISSIONS_TEMPLATES:
                    xp_reward = config.DAILY_MISSIONS_TEMPLATES[mission_name].get('xp_reward', 50)
                    coins_reward = config.DAILY_MISSIONS_TEMPLATES[mission_name].get('coins_reward', 5)
                    mission_display_name = config.DAILY_MISSIONS_TEMPLATES[mission_name].get('name', mission_name)
            except:
                pass
            
            # Update user rewards
            user = supabase.table('users').select('xp,coins').eq('user_id', user_id).single().execute().data
            if user:
                supabase.table('users').update({
                    'xp': user['xp'] + xp_reward,
                    'coins': user['coins'] + coins_reward
                }).eq('user_id', user_id).execute()
            
            # Create notification for bot to send to user
            try:
                supabase.table('notifications').insert({
                    'user_id': user_id,
                    'notification_type': 'mission_complete',
                    'title': f'🎉 Missão Completada: {mission_display_name}',
                    'message': f'Sua missão foi aprovada pelo administrador!\n\n**Recompensas:**\n• +{xp_reward} XP\n• +{coins_reward} 🪙',
                    'xp_reward': xp_reward,
                    'coins_reward': coins_reward,
                    'status': 'pending',
                }).execute()
                logger.info(f"Notification created for user {user_id}")
            except Exception as notif_error:
                logger.warning(f"Could not create notification: {notif_error}")
            
            flash(f"✅ Missão aprovada! Usuário recebeu +{xp_reward} XP e +{coins_reward} 🪙", "success")
        else:
            flash("Missão não encontrada ou já completada", "error")
            
    except Exception as e:
        logger.error(f"Error completing mission: {e}")
        flash(f"Erro: {str(e)}", "error")
    
    return redirect(url_for('missions'))


# ═══════════════════════════════════════════════════════════════
# GERENCIAMENTO DE EVENTOS
# ═══════════════════════════════════════════════════════════════

def convert_utc_to_br(utc_time_str):
    """Converte horário UTC para horário brasileiro (UTC-3)"""
    if not utc_time_str:
        return None
    try:
        from datetime import datetime, timedelta
        # Parse ISO format
        if 'Z' in utc_time_str:
            utc_time_str = utc_time_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(utc_time_str)
        # Remove timezone info and subtract 3 hours
        dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
        br_time = dt_naive - timedelta(hours=3)
        return br_time.strftime('%Y-%m-%d %H:%M')
    except:
        return utc_time_str

@app.route('/events')
@login_required
def events():
    supabase = get_supabase()
    
    # Busca todos os eventos
    events_data = supabase.table('events').select('*').order('created_at', desc=True).limit(50).execute().data
    
    # Busca presenças por evento e converte horários
    for event in events_data:
        presences = supabase.table('event_presence').select('id', count='exact').eq('event_id', event['id']).execute()
        event['presence_count'] = presences.count or 0
        
        # Converte horários UTC para horário brasileiro
        if event.get('start_time'):
            event['start_time_br'] = convert_utc_to_br(event['start_time'])
        if event.get('end_time'):
            event['end_time_br'] = convert_utc_to_br(event['end_time'])
    
    # Stats
    active_events = len([e for e in events_data if e.get('is_active')])
    total_events = len(events_data)
    
    stats = {
        'active': active_events,
        'total': total_events,
    }
    
    return render_template('events.html', 
                           events=events_data, 
                           stats=stats,
                           title="Gerenciar Eventos", 
                           active_page='events')


@app.route('/events/create', methods=['POST'])
@login_required
def create_event():
    try:
        from datetime import datetime, timedelta
        
        name = request.form.get('name')
        event_type = request.form.get('event_type', 'event')
        xp_reward = int(request.form.get('xp_reward', 100))
        coins_reward = int(request.form.get('coins_reward', 10))
        description = request.form.get('description', '')
        
        # Horários (em horário brasileiro - convertemos para UTC)
        event_date = request.form.get('event_date')  # YYYY-MM-DD
        start_time_str = request.form.get('start_time')  # HH:MM
        end_time_str = request.form.get('end_time')  # HH:MM
        
        supabase = get_supabase()
        
        data = {
            'event_name': name,
            'event_type': event_type,
            'xp_reward': xp_reward,
            'coins_reward': coins_reward,
            'description': description,
            'is_active': True,
        }
        
        # Converte horários locais (BR) para UTC (+3 horas)
        if event_date and start_time_str and end_time_str:
            start_datetime = datetime.strptime(f"{event_date} {start_time_str}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{event_date} {end_time_str}", "%Y-%m-%d %H:%M")
            
            # Adiciona 3 horas para converter BR -> UTC
            start_utc = start_datetime + timedelta(hours=3)
            end_utc = end_datetime + timedelta(hours=3)
            
            data['start_time'] = start_utc.isoformat()
            data['end_time'] = end_utc.isoformat()
        
        result = supabase.table('events').insert(data).execute()
        
        if result.data:
            event_id = result.data[0]['id']
            flash(f"✅ Evento '{name}' criado com sucesso! (ID: {event_id})", "success")
        else:
            flash("Erro ao criar evento", "error")
            
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        flash(f"Erro: {str(e)}", "error")
    
    return redirect(url_for('events'))


@app.route('/events/end', methods=['POST'])
@login_required
def end_event():
    try:
        event_id = int(request.form.get('event_id'))
        
        supabase = get_supabase()
        supabase.table('events').update({
            'is_active': False
        }).eq('id', event_id).execute()
        
        flash(f"✅ Evento #{event_id} encerrado!", "success")
    except Exception as e:
        logger.error(f"Error ending event: {e}")
        flash(f"Erro: {str(e)}", "error")
    
    return redirect(url_for('events'))


if __name__ == '__main__':
    print("🦈 SharkClub Dashboard rodando em http://localhost:5000")
    print(f"🔑 Senha de admin: {ADMIN_PASSWORD}")
    app.run(debug=True, port=5000)

