-- ==============================================================================
-- Zoe Multi-Tenant SaaS Platform Schema (Supabase / PostgreSQL)
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Projects Table
-- Stores tenant projects with Fernet AES-256 encrypted bot tokens
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    telegram_bot_token TEXT NOT NULL,
    telegram_group_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Row Level Security (RLS)
-- Ensures complete multi-tenant isolation: users only see and manage their own projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view only their own projects
CREATE POLICY "Users can read own projects" 
    ON public.projects 
    FOR SELECT 
    USING (auth.uid() = owner_id);

-- Policy: Users can insert their own projects
CREATE POLICY "Users can insert own projects" 
    ON public.projects 
    FOR INSERT 
    WITH CHECK (auth.uid() = owner_id);

-- Policy: Users can update their own projects
CREATE POLICY "Users can update own projects" 
    ON public.projects 
    FOR UPDATE 
    USING (auth.uid() = owner_id);

-- Policy: Users can delete their own projects
CREATE POLICY "Users can delete own projects" 
    ON public.projects 
    FOR DELETE 
    USING (auth.uid() = owner_id);

-- Index for high-speed queries by owner
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON public.projects(owner_id);

