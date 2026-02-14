-- === ASC 340-40 costs =====================================
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

-- === Locking ==============================================
create table if not exists schedule_locks (
  id bigserial primary key,
  contract_id text not null,
  schedule_hash text not null,
  approver_sub text not null,
  approver_email text,
  note text,
  locked_at timestamptz default now()
);
create index if not exists idx_schedule_locks_contract on schedule_locks(contract_id);

-- === RBAC new perms =======================================
insert into permissions (code, label)
values
  ('costs.run','Run costs amortization'),
  ('schedules.approve','Lock/unlock schedules')
on conflict (code) do nothing;

-- Grant to finance + admin
insert into role_permissions (role_id, permission_id)
select r.id, p.id
from roles r, permissions p
where r.code in ('admin','finance')
  and p.code in ('costs.run','schedules.approve')
on conflict do nothing;