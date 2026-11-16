-- Run this once in your Supabase project's SQL Editor.
-- It creates the one table used by storage.py.

create table if not exists public.tournaments (
    code text primary key,
    data jsonb not null,
    version integer not null default 0,
    created_at timestamptz not null default now()
);

-- This is a no-account party game. Anyone with the app link can read and join
-- its lobbies, so the browser may use the public anon key for these actions.
alter table public.tournaments enable row level security;

create policy "party players can read tournaments"
on public.tournaments for select to anon using (true);

create policy "party players can create tournaments"
on public.tournaments for insert to anon with check (true);

create policy "party players can update tournaments"
on public.tournaments for update to anon using (true) with check (true);
