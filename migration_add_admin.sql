-- Rode este comando no SQL Editor do Supabase para adicionar a coluna de admin
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Opcional: Definir seu usuário como admin (substitua o ID pelo seu ID do Discord)
-- UPDATE public.users SET is_admin = TRUE WHERE user_id = SEU_ID_DO_DISCORD;
