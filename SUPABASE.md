# Setting up accounts (Supabase)

Fulltime uses Supabase for accounts and storage. Until `config.js` has your project's
details, the site runs without accounts and ratings stay in each visitor's browser.

Live site: https://mhd11sinan.github.io/fulltime/

## 1. Create the Supabase project

1. Go to https://supabase.com and sign up (signing in with GitHub is quickest).
2. Click **New project**. Name it `fulltime`, pick the region closest to your users
   (for India, **Mumbai / ap-south-1**), and set a database password. Save the password
   somewhere safe; the app doesn't need it.
3. Wait a minute or two for the project to finish setting up.

## 2. Create the tables

1. In the project, open **SQL Editor** and click **New query**.
2. Paste the whole of [`supabase/schema.sql`](supabase/schema.sql) and click **Run**.
   You should see "Success. No rows returned".
3. Open **Table Editor** to check: you should see `profiles`, `match_logs`,
   `player_ratings` and `custom_matches`.

## 3. Tell Supabase where the site lives

**Authentication > URL Configuration**:

- **Site URL**: `https://mhd11sinan.github.io/fulltime/`
- **Redirect URLs**: add `https://mhd11sinan.github.io/fulltime/` and, for testing on your
  PC, `http://localhost:8000/`

## 4. Email and password sign-in

**Authentication > Sign In / Providers > Email**: make sure it's enabled and leave
**Confirm email** on, so people must click a link in their inbox before signing in.

Supabase's built-in email sender only allows a few emails an hour. That's fine for testing.
Before you invite lots of people, set up your own sender under
**Authentication > Emails > SMTP Settings** (for example with Resend or Brevo, which have
free plans).

## 5. Google sign-in

You need a Google OAuth client.

1. Go to https://console.cloud.google.com and create a project called `Fulltime`.
2. Open **Google Auth Platform** (search for "OAuth consent screen" if you can't find it)
   and click **Get started**:
   - App name: `Fulltime`; support email: your email.
   - Audience: **External**.
   - Contact email: your email. Agree and **Create**.
3. In Supabase, open **Authentication > Sign In / Providers > Google** and copy the
   **Callback URL** it shows (it looks like `https://<your-project>.supabase.co/auth/v1/callback`).
4. Back in Google, open **Clients > Create client**:
   - Application type: **Web application**, name `Fulltime`.
   - Authorised JavaScript origins: `https://mhd11sinan.github.io` and `http://localhost:8000`
   - Authorised redirect URIs: the Callback URL from step 3.
   - Click **Create**, then copy the **Client ID** and **Client secret**.
5. In Supabase's Google provider, turn it on, paste the Client ID and Client secret, and **Save**.
6. In Google, open **Audience** and click **Publish app**. While the app is in "Testing",
   only the test users you list there can sign in. Fulltime only asks for name and email,
   so publishing doesn't need Google's review.

## 6. Connect the site

1. In Supabase, open **Project Settings > API Keys** (or the **Connect** button at the top).
2. Copy the **Project URL** and the **publishable key** (starts with `sb_publishable_`;
   older projects call it the `anon` `public` key).
3. Put them in `config.js`:

       supabaseUrl: 'https://<your-project>.supabase.co',
       supabaseKey: 'sb_publishable_...'

4. Commit and push. GitHub Pages redeploys in a minute or two.

Both values are meant to be public: anyone can see them in the page source, and the
database rules in `schema.sql` decide what each visitor can read and change. **Never** put
the `secret` / `service_role` key or your database password in `config.js` or anywhere in
this repo.

## Checking it works

1. Open the live site. A **Sign in** button appears top right.
2. Create an account with email and password, confirm it from your inbox, sign in and pick
   a username.
3. If you had ratings in this browser before, the Profile tab offers to import them.
4. Log a match, then open your profile link (Profile tab > **Copy link**) in a private
   window: it should show your ratings without signing in.
5. Sign out and sign in with Google.
