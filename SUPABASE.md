# Setting up accounts (Supabase)

Fulltime accounts are a **username and a password**: no email, no Google. Supabase stores
the accounts and everyone's ratings. Until `config.js` has your project's details, the site
runs without accounts and ratings stay in each visitor's browser.

Live site: https://mhd11sinan.github.io/fulltime/

## How usernames work

Supabase's sign-in needs an email address for every account, so the app turns each
username into a placeholder address, `<username>@users.fulltime.invalid`. `.invalid` is a
domain reserved so it can never receive mail, and nothing is ever sent there. People only
ever see and type their username.

Two things follow from that:

- **There's no "forgot password".** With no real email, people can't reset a lost password
  themselves. Signed-in users can change theirs from their profile (**Change password**).
  If someone is locked out, you can set a temporary password for them in **SQL Editor**
  (replace both values), tell them privately, and ask them to change it:

      update auth.users
      set encrypted_password = extensions.crypt('temporary-password', extensions.gen_salt('bf'))
      where email = 'their_username@users.fulltime.invalid';
- **Usernames can't be changed** after sign-up, because the sign-in address is built from them.

## 1. Create the Supabase project

1. Go to https://supabase.com and sign up (signing in with GitHub is quickest).
2. Click **New project**. Name it `fulltime`, pick the region closest to your users
   (for India, **Mumbai / ap-south-1**), and set a database password. Save the password
   somewhere safe; the app doesn't need it.
3. Wait a minute or two for the project to finish setting up.

## 2. Create the tables

1. Open https://raw.githubusercontent.com/mhd11sinan/fulltime/main/supabase/schema.sql,
   press **Ctrl+A** then **Ctrl+C**.
2. In Supabase, open **SQL Editor**, click **New query**, paste with **Ctrl+V**, and click **Run**.
   You should see "Success. No rows returned".
3. Open **Table Editor**. You should see seven tables: `profiles`, `match_logs`,
   `player_ratings`, `custom_matches`, `match_likes`, `watchlist` and `lists`.

The script also adds a trigger that creates each person's profile at the moment they sign up.

**Updating an existing project:** when new features need database changes, they come as files in
[`supabase/migrations/`](supabase/migrations/). Run each new one once in the SQL Editor the same way.
`schema.sql` already includes them, so a fresh project only needs `schema.sql`.

## 3. Turn on username sign-in

Open **Authentication > Sign In / Providers**:

1. Make sure **Allow new users to sign up** is on.
2. Open **Email** and make sure it's **enabled**.
3. Turn **Confirm email** **off** and click **Save**. This is required: with it on, nobody
   could finish signing up, because the placeholder addresses can't receive the
   confirmation email.

Optional, under **Authentication > Sign In / Providers > Email** or **Auth > Policies**
depending on your dashboard version: set the minimum password length to 8 to match the app,
and turn on leaked-password protection if your plan offers it.

## 4. Connect the site

1. In Supabase, open **Project Settings > API Keys** (or the **Connect** button at the top).
2. Copy the **Project URL** and the **publishable key** (starts with `sb_publishable_`;
   older projects call it the `anon` `public` key).
3. Put them in `config.js`:

       supabaseUrl: 'https://<your-project>.supabase.co',
       supabaseKey: 'sb_publishable_...',

4. Commit and push. GitHub Pages redeploys in a minute or two.

Both values are meant to be public: anyone can see them in the page source, and the
database rules in `schema.sql` decide what each visitor can read and change. **Never** put
the `secret` / `service_role` key or your database password in `config.js` or anywhere in
this repo.

## Checking it works

1. Open the live site (press **Ctrl+F5** to skip any cached copy). A **Sign in** button
   appears top right.
2. Click **Sign in > Create an account**, choose a username and password. You should be
   signed in straight away, with your username at the top right.
3. If you had ratings in this browser before, the Profile tab offers to import them.
4. Log a match, then open your profile link (Profile tab > **Copy link**) in a private
   window: it should show your ratings without signing in.
5. Sign out, then sign back in with the same username and password.

## If something goes wrong

- **"That username is taken or not allowed"** for every username: the trigger couldn't create
  the profile. Check that the whole of `schema.sql` ran without errors.
- **"Sign-in is blocked because Confirm email is on"**: redo step 3.
- **"The server rejected the account"**: Supabase refused the placeholder address. Tell
  Claude; the fix is to change `authEmailDomain` in `config.js`, which must happen before
  anyone signs up.
