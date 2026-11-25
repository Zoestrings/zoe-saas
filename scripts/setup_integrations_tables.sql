-- Supabase Schema for Multi-Tenant Telegram & Discord Integration Management (Stage B)

CREATE TABLE IF NOT EXISTS public.platform_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'discord')),
    bot_username TEXT,
    bot_external_id TEXT,
    encrypted_token TEXT,
    token_hash TEXT,
    encrypted_secret TEXT,
    status TEXT NOT NULL DEFAULT 'connected' CHECK (status IN ('connected', 'disconnected', 'error')),
    permissions_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_platform_integrations_project ON public.platform_integrations(project_id);
CREATE INDEX IF NOT EXISTS idx_platform_integrations_owner ON public.platform_integrations(owner_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_integrations_token_hash
    ON public.platform_integrations(token_hash)
    WHERE token_hash IS NOT NULL AND status = 'connected';

CREATE TABLE IF NOT EXISTS public.telegram_communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.platform_integrations(id) ON DELETE CASCADE,
    chat_id TEXT NOT NULL,
    chat_title TEXT,
    chat_type TEXT DEFAULT 'supergroup',
    is_admin_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_communities_integration ON public.telegram_communities(integration_id);

CREATE TABLE IF NOT EXISTS public.discord_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.platform_integrations(id) ON DELETE CASCADE,
    guild_id TEXT NOT NULL,
    guild_name TEXT,
    channel_id TEXT,
    permissions_bitmask TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discord_servers_integration ON public.discord_servers(integration_id);

CREATE TABLE IF NOT EXISTS public.integration_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES public.platform_integrations(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_integration_logs_integration ON public.integration_activity_logs(integration_id, created_at DESC);

-- Row-Level Security (Strict Multi-Tenant Isolation)
ALTER TABLE public.platform_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telegram_communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_servers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integration_activity_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Owners manage own platform integrations" ON public.platform_integrations;
CREATE POLICY "Owners manage own platform integrations" ON public.platform_integrations
    FOR ALL USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS "Owners manage own telegram communities" ON public.telegram_communities;
CREATE POLICY "Owners manage own telegram communities" ON public.telegram_communities
    FOR ALL USING (
        integration_id IN (SELECT id FROM public.platform_integrations WHERE owner_id = auth.uid())
    );

DROP POLICY IF EXISTS "Owners manage own discord servers" ON public.discord_servers;
CREATE POLICY "Owners manage own discord servers" ON public.discord_servers
    FOR ALL USING (
        integration_id IN (SELECT id FROM public.platform_integrations WHERE owner_id = auth.uid())
    );

DROP POLICY IF EXISTS "Owners view own integration logs" ON public.integration_activity_logs;
CREATE POLICY "Owners view own integration logs" ON public.integration_activity_logs
    FOR SELECT USING (
        integration_id IN (SELECT id FROM public.platform_integrations WHERE owner_id = auth.uid())
    );
