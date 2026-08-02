-- Run in Supabase SQL editor (or via psql) for greenfield setup.
-- Prefer Alembic migrations when using DATABASE_URL against Supabase.

create table if not exists leads (
  id uuid primary key,
  first_name varchar(100) not null,
  last_name varchar(100) not null,
  email varchar(320) not null,
  resume_path varchar(512) not null,
  resume_filename varchar(255) not null,
  resume_content_type varchar(128) not null,
  status varchar(32) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_leads_email on leads (email);
create index if not exists ix_leads_status on leads (status);

alter table leads add column if not exists reached_out_by varchar(128);
alter table leads add column if not exists reached_out_by_email varchar(320);
alter table leads add column if not exists reached_out_at timestamptz;

create table if not exists email_outbox (
  id uuid primary key,
  lead_id uuid not null references leads(id) on delete cascade,
  template varchar(64) not null,
  to_email varchar(320) not null,
  subject varchar(255) not null,
  body_text text not null,
  status varchar(32) not null,
  attempts integer not null default 0,
  next_attempt_at timestamptz not null default now(),
  last_error text,
  provider_message_id varchar(255),
  idempotency_key varchar(128) not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ix_email_outbox_lead_id on email_outbox (lead_id);
create index if not exists ix_email_outbox_status on email_outbox (status);
create index if not exists ix_email_outbox_next_attempt_at on email_outbox (next_attempt_at);

-- Storage: create a private bucket named "resumes" in the Supabase dashboard
-- with allowed MIME types PDF/DOC/DOCX and a 10MB file size limit.
-- API uses the service role key and does not rely on Storage RLS for uploads.
