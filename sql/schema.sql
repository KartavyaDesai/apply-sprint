-- ApplySprint V1 schema. Run this once in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.applications (
    id uuid primary key default gen_random_uuid(),
    university_name text not null,
    program_name text not null,
    program_url text not null,
    admission_url text,
    application_deadline date,
    intake text,
    additional_context text,
    status text not null default 'active' check (status in ('active','completed','archived')),
    source_documents jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.timeline_items (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references public.applications(id) on delete cascade,
    title text not null,
    description text not null,
    due_date date,
    is_completed boolean not null default false,
    sort_order integer not null default 1,
    date_type text not null default 'unknown' check (date_type in ('official','recommended','unknown')),
    source_reference text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.timeline_notes (
    id uuid primary key default gen_random_uuid(),
    timeline_item_id uuid not null unique references public.timeline_items(id) on delete cascade,
    note text,
    attachments jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_applications_created_at on public.applications(created_at desc);
create index if not exists idx_timeline_items_application_order on public.timeline_items(application_id, sort_order);
create index if not exists idx_timeline_items_due_date on public.timeline_items(due_date);

-- Create a private Storage bucket named "application-documents".
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('application-documents', 'application-documents', false, 15728640,
        array['application/pdf','image/png','image/jpeg','text/plain',
              'application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
on conflict (id) do nothing;

-- V1 server-side service-role access is used by FastAPI. Never expose the service role key to browsers.
-- If you add Supabase Auth later, add owner_id columns, enable RLS, and scope every query to auth.uid().
