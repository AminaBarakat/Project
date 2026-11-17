-- Run this once in your Supabase project's SQL Editor.
-- It creates the one table used by storage.py.

create table if not exists public.tournaments (
    code text primary key,
    data jsonb not null,
    version integer not null default 0,
    created_at timestamptz not null default now()
);

-- Tournament JSON includes private Round 2 duo/card assignments. Only the
-- Streamlit server may read it, using its service_role key from Streamlit secrets.
alter table public.tournaments enable row level security;

-- Remove the old open policies if this script is being applied to an existing project.
drop policy if exists "party players can read tournaments" on public.tournaments;
drop policy if exists "party players can create tournaments" on public.tournaments;
drop policy if exists "party players can update tournaments" on public.tournaments;

-- The service_role connection is server-side and bypasses RLS. Anonymous and
-- authenticated browser clients have no table policies and cannot read/write rows.
revoke all on public.tournaments from anon, authenticated;
