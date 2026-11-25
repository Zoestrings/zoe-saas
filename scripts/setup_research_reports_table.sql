-- Supabase Schema for Autonomous Research Reports (Pillar 3)
CREATE TABLE IF NOT EXISTS public.research_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    report_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_research_reports_project_created
    ON public.research_reports(project_id, created_at DESC);

ALTER TABLE public.research_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Project owners can view own reports" ON public.research_reports;
CREATE POLICY "Project owners can view own reports" ON public.research_reports
    FOR SELECT USING (
        project_id IN (SELECT id FROM public.projects WHERE owner_id = auth.uid())
    );
