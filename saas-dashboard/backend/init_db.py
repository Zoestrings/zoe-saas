"""Database initialization & migration helper for Zoe SaaS Dashboard."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

PROJECTS_TABLE_SQL = """-- ========================================================
-- Zoe SaaS Dashboard: Projects Table & RLS Setup
-- Run this in your Supabase Dashboard -> SQL Editor
-- ========================================================

-- Enable pgcrypto extension for UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create projects table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    telegram_bot_token TEXT NOT NULL,
    telegram_group_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS) on projects table
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS "Users can view their own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can insert their own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can update their own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can delete their own projects" ON public.projects;

-- Policy 1: Users can view their own projects
CREATE POLICY "Users can view their own projects"
    ON public.projects FOR SELECT
    USING (auth.uid() = owner_id);

-- Policy 2: Users can insert their own projects
CREATE POLICY "Users can insert their own projects"
    ON public.projects FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

-- Policy 3: Users can update their own projects
CREATE POLICY "Users can update their own projects"
    ON public.projects FOR UPDATE
    USING (auth.uid() = owner_id);

-- Policy 4: Users can delete their own projects
CREATE POLICY "Users can delete their own projects"
    ON public.projects FOR DELETE
    USING (auth.uid() = owner_id);
"""


def check_supabase_connection():
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")

    print("\n" + "=" * 60)
    print("Zoe SaaS Dashboard — Supabase Database Setup")
    print("=" * 60)

    if not supabase_url or "your-project" in supabase_url or not supabase_key:
        print("[!] Note: SUPABASE_URL and SUPABASE_KEY are currently using template/placeholder values in .env.")
        print("    Update saas-dashboard/backend/.env with your real Supabase credentials.")
    else:
        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            print("[+] Successfully initialized Supabase client connection.")
        except Exception as exc:
            print(f"[!] Warning connecting to Supabase: {exc}")

    print("\n--- COPY AND PASTE THIS SQL INTO SUPABASE SQL EDITOR ---\n")
    print(PROJECTS_TABLE_SQL)
    print("=" * 60)


if __name__ == "__main__":
    check_supabase_connection()

