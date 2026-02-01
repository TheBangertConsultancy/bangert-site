# THE BANGERT CONSULTANCY
# Complete Deployment Guide: From Wix to Your Own Site

---

## WHAT'S IN THIS PACKAGE

```
bangert-site/
  index.html              <- Your entire website (single file, everything included)
  netlify.toml            <- Netlify configuration (caching, redirects, security)
  robots.txt              <- Tells Google how to crawl your site
  sitemap.xml             <- Tells Google what pages exist
  news_agent.py           <- Python script that fetches tourism news automatically
  news_feed.json          <- (will be generated) News data your site displays
  .github/
    workflows/
      news_agent.yml      <- GitHub Actions config to run news agent every 6 hours
  images/
    hero/
      README.txt          <- Instructions for hero slideshow photos
      slide-1.jpg          (YOU ADD: wide shot on stage)
      slide-2.jpg          (YOU ADD: conference setting)
      slide-3.jpg          (YOU ADD: workshop delivery)
      slide-4.jpg          (YOU ADD: destination photo)
      slide-5.jpg          (YOU ADD: professional shot)
    about/
      README.txt          <- Instructions for about section photos
      headshot.jpg         (YOU ADD: professional headshot)
      speaking.jpg         (YOU ADD: presenting photo)
      conference.jpg       (YOU ADD: casual professional)
    logos/
      README.txt          <- Instructions for client logos
    og-image.jpg           (YOU ADD: 1200x630px image for social sharing)
    favicon-32x32.png      (YOU ADD: favicon)
    favicon-16x16.png      (YOU ADD: favicon)
    apple-touch-icon.png   (YOU ADD: 180x180px icon)
```

---

## STEP 1: ADD YOUR PHOTOS (10 minutes)

Before deploying, add your images. The site works without them (shows solid
colours as fallback), but obviously looks much better with real photos.

### Hero slideshow (5 photos)
Save these into `images/hero/`:
- `slide-1.jpg` - You on stage at IQ Digital or similar (wide shot, audience visible)
- `slide-2.jpg` - Discover North-East Conference or similar event
- `slide-3.jpg` - Workshop delivery (you interacting with participants)
- `slide-4.jpg` - Destination landscape (Mamaia coastline, Moldova vineyards)
- `slide-5.jpg` - Panel discussion, networking event, or destination visit

Specs: 1920x1080px, JPG, under 400KB each.
Compress at https://tinypng.com before adding.

### About section (3 photos)
Save these into `images/about/`:
- `headshot.jpg` - Your professional headshot
- `speaking.jpg` - You presenting (different angle from hero)
- `conference.jpg` - Casual professional setting

Specs: 800x1000px, JPG, portrait orientation.

### Social sharing image
Save into `images/`:
- `og-image.jpg` - 1200x630px image shown when your site link is shared on
  LinkedIn, Facebook, WhatsApp, etc. Use your headshot with the logo and
  tagline overlaid, or a professional photo with a text overlay.

### Favicon
Generate at https://favicon.io using your logo or the "B" monogram.
Download the package and place the files in `images/`.

---

## STEP 2: CREATE A GITHUB ACCOUNT (5 minutes, if you don't have one)

1. Go to https://github.com
2. Click "Sign up"
3. Create your account (free)

You need GitHub for two things:
- Hosting your site files (Netlify pulls from here)
- Running the news agent automatically (GitHub Actions)

---

## STEP 3: CREATE YOUR GITHUB REPOSITORY (5 minutes)

1. Log into GitHub
2. Click the green "New" button (or go to https://github.com/new)
3. Repository name: `bangert-site`
4. Set to **Public** (needed for Netlify free tier and GitHub Pages)
5. Do NOT initialise with README (we have our own files)
6. Click "Create repository"

### Upload your files:

**Easiest method (drag and drop):**
1. On the repository page, click "uploading an existing file"
2. Drag the entire contents of the `bangert-site/` folder into the browser
3. Write commit message: "Initial site deployment"
4. Click "Commit changes"

**Note:** GitHub's web uploader doesn't handle nested folders well. 
You may need to:
- Upload root files first (index.html, netlify.toml, etc.)
- Then create `images/hero/` folder and upload photos there
- Then create `images/about/` folder and upload photos there
- Then create `.github/workflows/` folder and upload news_agent.yml there

**Better method (if comfortable with terminal):**
```bash
cd bangert-site
git init
git add .
git commit -m "Initial site deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bangert-site.git
git push -u origin main
```

---

## STEP 4: DEPLOY ON NETLIFY (10 minutes)

1. Go to https://www.netlify.com
2. Click "Sign up" and choose "Sign up with GitHub"
3. Authorise Netlify to access your GitHub account
4. Click "Add new site" > "Import an existing project"
5. Choose "GitHub"
6. Select your `bangert-site` repository
7. Build settings:
   - Build command: (leave empty)
   - Publish directory: `.`  (just a single dot)
8. Click "Deploy site"

Netlify will deploy in about 30 seconds. You'll get a random URL like
`random-name-123.netlify.app`. Click it to see your live site.

---

## STEP 5: CONNECT YOUR DOMAIN (15 minutes)

### In Netlify:
1. Go to your site dashboard on Netlify
2. Click "Domain management" (or "Set up a custom domain")
3. Click "Add a custom domain"
4. Enter: `www.thebangertconsultancy.com`
5. Netlify will show you DNS records to add

### At your domain registrar:
You need to find where you bought `thebangertconsultancy.com` and update
the DNS settings. Common registrars: GoDaddy, Namecheap, Google Domains, etc.

**Remove the old Wix DNS records** (the CNAME or A records pointing to Wix).

**Add the Netlify DNS records.** Netlify will tell you exactly what to add.
Typically:
- A record: `@` pointing to `75.2.60.5` (Netlify's load balancer)
- CNAME record: `www` pointing to `your-site.netlify.app`

Or, even easier: switch to Netlify DNS entirely:
1. In Netlify, go to Domain management > Netlify DNS
2. Click "Activate Netlify DNS"
3. Netlify gives you nameservers (like `dns1.p01.nsone.net`)
4. Go to your registrar and update nameservers to Netlify's nameservers
5. This gives Netlify full control and auto-configures everything

### SSL Certificate:
Netlify automatically provisions a free SSL certificate (HTTPS).
This happens automatically once DNS propagates (can take 5 min to 48 hours,
usually under 1 hour).

### Cancel Wix:
Once your new site is live and working on your domain, you can cancel
your Wix subscription. Don't cancel before confirming the new site works.

---

## STEP 6: SET UP THE NEWS FEED (15 minutes)

You have two options. I recommend Option A.

### Option A: News feed in the same repository (simplest)

Your news_agent.py and .github/workflows/news_agent.yml are already in the
repository. GitHub Actions will run the agent every 6 hours, generate
news_feed.json, commit it to the repo, and Netlify will auto-deploy.

1. Go to your GitHub repo
2. Click the "Actions" tab
3. You should see "Update Tourism News Feed" workflow
4. Click "Run workflow" > "Run workflow" to test it manually
5. Wait 1-2 minutes for it to complete
6. Check that `news_feed.json` appeared in your repository
7. Visit your site - the news section should now show live articles

That's it. It runs automatically every 6 hours from now on. Every time
it updates news_feed.json, Netlify detects the change and redeploys
(takes about 30 seconds).

### Option B: Separate repository for the news feed

If you want the news feed on a separate schedule from the main site:

1. Create a new repo called `bangert-news-feed`
2. Upload only `news_agent.py` and `.github/workflows/news_agent.yml`
3. Enable GitHub Pages on that repo (Settings > Pages > main branch)
4. In your main site's `index.html`, update the FEED_URL:
   ```javascript
   const FEED_URL = 'https://YOUR_USERNAME.github.io/bangert-news-feed/news_feed.json';
   ```
5. Redeploy the main site

---

## STEP 7: VERIFY EVERYTHING WORKS

### Checklist:

- [ ] Site loads at https://www.thebangertconsultancy.com
- [ ] HTTPS (padlock icon) is working
- [ ] Navigation links scroll smoothly to sections
- [ ] Hero slideshow rotates through photos
- [ ] About slideshow rotates through photos
- [ ] YouTube video plays in the Speaking section
- [ ] Contact form submits (test with your own email)
- [ ] Calendly link opens booking page
- [ ] News section shows articles (after running the agent)
- [ ] Mobile layout works (test on your phone)
- [ ] Share the URL on LinkedIn and check the preview shows your og-image

---

## ONGOING MAINTENANCE

### To update text or content:
1. Edit `index.html` in your GitHub repository (click the file, then pencil icon)
2. Make your change
3. Click "Commit changes"
4. Netlify auto-deploys in 30 seconds

### To swap photos:
1. Go to `images/hero/` or `images/about/` in your GitHub repo
2. Delete the old file
3. Upload the new file with the SAME filename
4. Netlify auto-deploys

### To add a new testimonial:
1. Edit `index.html`
2. Find the testimonials section
3. Copy one of the existing testimonial-card blocks
4. Replace the text, name, and role
5. Commit

### News feed runs automatically.
Check the Actions tab occasionally to make sure it's not failing.
If an RSS feed goes down, the agent handles it gracefully and just
skips that source.

---

## COST COMPARISON

### What you're paying now (Wix):
- Wix Business plan: ~$17-32/month ($204-384/year)
- Custom domain connection: included
- Total: $200-400/year

### What you'll pay with this setup:
- Netlify hosting: $0 (free tier, more than enough for a consultancy site)
- GitHub: $0 (free tier)
- GitHub Actions for news feed: $0 (2,000 free minutes/month, you use ~60)
- Domain renewal: ~$12-15/year (you already pay this)
- Total: $12-15/year

Annual savings: roughly $190-370.

### What you get that Wix doesn't give you:
- Full code ownership (no platform lock-in)
- Faster load times (static HTML vs Wix's bloated runtime)
- Better SEO (clean code, no Wix overhead)
- Complete control over every pixel
- Auto-updating news feed
- No "Made with Wix" branding
- Version history for every change (Git)

---

## TROUBLESHOOTING

**"My domain isn't working after DNS change"**
DNS can take up to 48 hours to propagate. Usually it's 15-60 minutes.
Check status at https://www.whatsmydns.net

**"The news feed isn't showing articles"**
1. Check GitHub Actions tab - is the workflow running?
2. Check that news_feed.json exists in your repo
3. Check browser console (F12) for JavaScript errors
4. Make sure the FEED_URL in index.html is correct

**"Images aren't showing"**
1. Check filenames match exactly (case-sensitive): slide-1.jpg not Slide-1.JPG
2. Make sure images are in the correct folder
3. Check file size - GitHub has a 100MB file limit

**"Contact form isn't working"**
The form uses FormSubmit.co (free service). On first submission, you'll get
a confirmation email from FormSubmit. Click the confirmation link.
After that, all submissions go to thomas@thebangertconsultancy.com.

**"I need help making changes"**
Just ask me. I can edit any part of the site, add new sections, update
content, or adjust the design.
