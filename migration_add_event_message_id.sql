-- Adiciona colunas para rastrear anúncios de eventos e o canal onde foram postados
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS message_id text,
ADD COLUMN IF NOT EXISTS channel_id text;

-- Opcional: Index para performance em lookups nulos (usado na query get_unannounced_events)
CREATE INDEX IF NOT EXISTS idx_events_message_id ON events(message_id);
