-- ============================================================
-- AccrueSmart – Supabase / PostgreSQL Schema
-- Run once against your Supabase project (SQL Editor → New Query)
-- ============================================================

-- === RBAC BASE TABLES ========================================
-- These must exist before the permission inserts at the bottom.

create table if not exists roles (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,          -- e.g. "finance", "deal_desk", "auditor", "admin"
  label text not null default '',
  created_at timestamptz default now()
);

create table if not exists permissions (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,          -- e.g. "product.manage"
  label text not null default '',
  created_at timestamptz default now()
);

create table if not exists role_permissions (
  role_id uuid references roles(id) on delete cascade,
  permission_id uuid references permissions(id) on delete cascade,
  primary key (role_id, permission_id)
);

-- Seed a few default roles
-- SAFE ADD: includes 'admin' because later grants reference it
insert into roles (code, label) values
  ('admin',     'System admin'),
  ('finance',   'Finance team'),
  ('deal_desk', 'Deal-desk / sales ops'),
  ('auditor',   'External / internal auditor')
on conflict (code) do nothing;

-- Seed permissions already referenced in routers
insert into permissions (code, label) values
  ('schedules.approve', 'Approve revenue schedules'),
  ('deal.view',         'View deal data'),
  ('revrec.export',     'Export revrec data'),
  ('reports.memo',      'Generate audit memos'),
  ('leases.edit',       'Edit lease records'),
  ('leases.export',     'Export lease data'),
  ('costs.run',         'Run cost amortisation')
on conflict (code) do nothing;


-- === PRODUCT CATALOG + REVREC CODES =========================

create table if not exists product_codes (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  description text default '',
  created_at timestamptz default now()
);

create table if not exists revrec_codes (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  rule_type text not null check (rule_type in (
    'straight_line','point_in_time','milestone','percent_complete','usage'
  )),
  params jsonb not null default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Many:1 map – each product has one default revrec code
create table if not exists product_revrec_map (
  product_id uuid references product_codes(id) on delete cascade,
  revrec_id  uuid references revrec_codes(id) on delete restrict,
  primary key (product_id)
);

-- Convenience view: product catalog with revrec info
create or replace view product_catalog as
select p.id, p.code, p.name,
       r.code as revrec_code, r.rule_type, r.params
from   product_codes p
left join product_revrec_map m on m.product_id = p.id
left join revrec_codes r       on r.id = m.revrec_id;


-- === ASC 340-40 COSTS ========================================

create table if not exists contract_costs (
  id uuid primary key default gen_random_uuid(),
  contract_id text not null,
  label text,
  amount numeric not null,
  start_date date not null,
  months int not null check (months > 0),
  method text not null default 'straight_line', -- 'straight_line' | 'percent_complete' | 'custom_curve'
  curve numeric[] default null,
  created_at timestamptz default now()
);


-- === SCHEDULE LOCK ===========================================
-- KEEPING your existing table name (schedulelock) so nothing breaks.
create table if not exists schedulelock (
  id serial primary key,
  contract_id text not null,
  schedule_hash text not null,
  approver_sub text not null,
  approver_email text,
  note text,
  locked_at timestamptz default now()
);
create index if not exists ix_schedulelock_contract
  on schedulelock (contract_id);

-- SAFE ADD: also create the spec-aligned table name schedule_locks.
-- This does NOT break anything; it just ensures Task 6 matches expected naming too.
create table if not exists schedule_locks (
  id bigserial primary key,
  contract_id text not null,
  schedule_hash text not null,
  approver_sub text not null,
  approver_email text,
  note text,
  locked_at timestamptz default now()
);
create index if not exists idx_schedule_locks_contract
  on schedule_locks (contract_id);


-- === SCHEDULES (persisted output from the engine) ============

create table if not exists schedules (
  id serial primary key,
  contract_id text not null,
  po_id text not null,
  period text not null,               -- "2025-01"
  amount numeric not null,
  product_code text,
  revrec_code text,
  created_at timestamptz default now()
);
create index if not exists ix_schedules_contract
  on schedules (contract_id);


-- === SCHEDULES EDIT (user / AI grid overrides) ===============

create table if not exists schedules_edit (
  contract_id text not null,
  line_no int not null,
  period text not null,
  amount numeric not null,
  product_code text,
  revrec_code text,
  source text default 'user',         -- 'user' | 'ai' | 'rule'
  primary key (contract_id, line_no, period)
);


-- === ADDITIONAL PERMISSIONS ==================================

insert into permissions (code, label) values
  ('product.manage',    'Manage product codes'),
  ('revrec.manage',     'Manage revrec codes'),
  ('schedules.edit',    'Edit revrec schedules'),
  ('schedules.import',  'Import grid schedules'),
  ('schedules.export',  'Export grid schedules')
on conflict (code) do nothing;

-- Grant finance + deal_desk the new powers
insert into role_permissions (role_id, permission_id)
select r.id, p.id
from   roles r, permissions p
where  r.code in ('finance','deal_desk')
  and  p.code in (
    'product.manage','revrec.manage',
    'schedules.edit','schedules.import','schedules.export'
  )
on conflict do nothing;

-- Grant admin + finance the costs & lock powers (from master)
-- SAFE now because admin role exists above
insert into role_permissions (role_id, permission_id)
select r.id, p.id
from roles r, permissions p
where r.code in ('admin','finance')
  and p.code in ('costs.run','schedules.approve')
on conflict do nothing;
