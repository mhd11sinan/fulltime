// Supabase project settings. Both values are meant to be public: the database's
// row-level security rules (supabase/schema.sql) decide what each visitor can
// read and change. Never put the secret or service_role key here.
// Leave them empty to run Fulltime without accounts (ratings stay in the browser).
window.FULLTIME_CONFIG = {
  supabaseUrl: 'https://prpgwmtburkgirucoolb.supabase.co', // e.g. https://abcdefghijklmnop.supabase.co
  supabaseKey: 'sb_publishable_Z1Pt9j5JKvAYBj3vgOY3Yg_YPdmD5jC', // the project's publishable key (sb_publishable_...) or legacy anon key
  // Accounts are username + password. Supabase still needs an email address per account,
  // so the app uses <username>@<this domain>; nothing is ever sent there. Only change it
  // if Supabase rejects these addresses, and never after people have signed up.
  authEmailDomain: 'users.fulltime.invalid'
};
