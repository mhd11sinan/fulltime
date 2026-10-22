-- Adds the favourite club and the personal club and player rankings to profiles.
-- Run once in Supabase (SQL Editor > New query > paste > Run) on a database that was
-- created from schema.sql before these columns existed. Safe to run twice.

alter table public.profiles
  add column if not exists fav_team text not null default '' check (char_length(fav_team) <= 40),
  add column if not exists team_rank text[] not null default '{}' check (cardinality(team_rank) <= 40),
  add column if not exists player_rank text[] not null default '{}' check (cardinality(player_rank) <= 100);
