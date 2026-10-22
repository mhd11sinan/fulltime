-- Fulltime database. Run once in Supabase: SQL Editor > New query > paste all of this > Run.
--
-- Everything is publicly readable (profiles are public, like Letterboxd).
-- Row-level security makes sure each signed-in user can only change their own rows.

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  username text not null unique check (username ~ '^[a-z0-9_]{3,20}$'),
  fav_matches text[] not null default '{}' check (cardinality(fav_matches) <= 4),
  fav_players text[] not null default '{}' check (cardinality(fav_players) <= 4),
  created_at timestamptz not null default now()
);

-- One row per match a user has logged. match_id is 'm1', 'm2', ... for seeded
-- matches (position in RAW in index.html) or 'c...' for the user's own custom matches.
create table public.match_logs (
  user_id uuid not null references public.profiles (id) on delete cascade,
  match_id text not null check (char_length(match_id) between 1 and 40),
  rating numeric(2,1) not null default 0 check (rating between 0 and 5 and rating * 2 = floor(rating * 2)),
  mode text not null default 'live' check (mode in ('live', 'replay', 'attended', 'highlights')),
  review text not null default '' check (char_length(review) <= 400),
  logged_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, match_id)
);
create index match_logs_match_id on public.match_logs (match_id);

create table public.player_ratings (
  user_id uuid not null references public.profiles (id) on delete cascade,
  player_id text not null check (char_length(player_id) between 1 and 100),
  name text not null check (char_length(name) between 1 and 60),
  team text not null check (char_length(team) <= 40),
  rating numeric(2,1) not null default 0 check (rating between 0 and 5 and rating * 2 = floor(rating * 2)),
  note text not null default '' check (char_length(note) <= 200),
  primary key (user_id, player_id)
);

-- Matches a user added by hand because they weren't in the seeded list yet.
create table public.custom_matches (
  user_id uuid not null references public.profiles (id) on delete cascade,
  id text not null check (id ~ '^c[a-z0-9]{1,39}$'),
  md smallint not null check (md between 1 and 9),
  match_date date not null,
  home text not null check (char_length(home) between 1 and 40),
  home_goals smallint not null check (home_goals between 0 and 99),
  away text not null check (char_length(away) between 1 and 40),
  away_goals smallint not null check (away_goals between 0 and 99),
  primary key (user_id, id)
);

create table public.match_likes (
  user_id uuid not null references public.profiles (id) on delete cascade,
  match_id text not null check (char_length(match_id) between 1 and 40),
  created_at timestamptz not null default now(),
  primary key (user_id, match_id)
);
create index match_likes_match_id on public.match_likes (match_id);

-- Watchlist entries name a fixture as 'YYYY-MM-DD_home-slug_away-slug', so an entry
-- added before kick-off still points at the match after it gets a result and an id.
create table public.watchlist (
  user_id uuid not null references public.profiles (id) on delete cascade,
  fixture text not null check (char_length(fixture) <= 140 and fixture ~ '^\d{4}-\d\d-\d\d_[a-z0-9-]+_[a-z0-9-]+$'),
  added_at timestamptz not null default now(),
  primary key (user_id, fixture)
);

-- Ordered lists of matches, like Letterboxd lists. items holds match ids in order.
create table public.lists (
  user_id uuid not null references public.profiles (id) on delete cascade,
  id text not null check (id ~ '^l[a-z0-9]{1,39}$'),
  name text not null check (char_length(name) between 1 and 60),
  description text not null default '' check (char_length(description) <= 300),
  items text[] not null default '{}' check (cardinality(items) <= 100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, id)
);

alter table public.profiles enable row level security;
alter table public.match_logs enable row level security;
alter table public.player_ratings enable row level security;
alter table public.custom_matches enable row level security;
alter table public.match_likes enable row level security;
alter table public.watchlist enable row level security;
alter table public.lists enable row level security;

create policy "Profiles are public" on public.profiles for select using (true);
create policy "Users create their own profile" on public.profiles for insert to authenticated with check ((select auth.uid()) = id);
create policy "Users update their own profile" on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy "Logs are public" on public.match_logs for select using (true);
create policy "Users add their own logs" on public.match_logs for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own logs" on public.match_logs for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users delete their own logs" on public.match_logs for delete to authenticated using ((select auth.uid()) = user_id);

create policy "Player ratings are public" on public.player_ratings for select using (true);
create policy "Users add their own player ratings" on public.player_ratings for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own player ratings" on public.player_ratings for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users delete their own player ratings" on public.player_ratings for delete to authenticated using ((select auth.uid()) = user_id);

create policy "Custom matches are public" on public.custom_matches for select using (true);
create policy "Users add their own matches" on public.custom_matches for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own matches" on public.custom_matches for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users delete their own matches" on public.custom_matches for delete to authenticated using ((select auth.uid()) = user_id);

create policy "Likes are public" on public.match_likes for select using (true);
create policy "Users add their own likes" on public.match_likes for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own likes" on public.match_likes for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users delete their own likes" on public.match_likes for delete to authenticated using ((select auth.uid()) = user_id);

create policy "Watchlists are public" on public.watchlist for select using (true);
create policy "Users add to their own watchlist" on public.watchlist for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own watchlist" on public.watchlist for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users remove from their own watchlist" on public.watchlist for delete to authenticated using ((select auth.uid()) = user_id);

create policy "Lists are public" on public.lists for select using (true);
create policy "Users create their own lists" on public.lists for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users edit their own lists" on public.lists for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "Users delete their own lists" on public.lists for delete to authenticated using ((select auth.uid()) = user_id);

grant select on public.profiles, public.match_logs, public.player_ratings, public.custom_matches,
  public.match_likes, public.watchlist, public.lists to anon, authenticated;
grant insert, update on public.profiles to authenticated;
grant insert, update, delete on public.match_logs, public.player_ratings, public.custom_matches,
  public.match_likes, public.watchlist, public.lists to authenticated;

-- Sign-up is username + password: the app sends the username as user metadata and
-- this trigger creates the profile in the same transaction as the account. If the
-- username is invalid or taken, the insert fails and so does the whole sign-up.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, username)
  values (new.id, lower(new.raw_user_meta_data ->> 'username'));
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
