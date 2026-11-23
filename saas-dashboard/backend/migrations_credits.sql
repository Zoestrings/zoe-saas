-- =========================================================================
-- Supabase SQL Migration: Pay-Per-Use Credit System & Top-Ups
-- =========================================================================

-- 1. Add credits column to entitlements table
ALTER TABLE public.entitlements 
ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0;

-- 2. Add invoice_type and credits to invoices table
ALTER TABLE public.invoices 
ADD COLUMN IF NOT EXISTS invoice_type TEXT DEFAULT 'subscription';

ALTER TABLE public.invoices 
ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0;

-- 3. Ensure dev_entitlements has credits default index if needed
CREATE INDEX IF NOT EXISTS idx_entitlements_user_id ON public.entitlements(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON public.invoices(user_id);
