# PreventVital marketing site

Premium landing page for PreventVital, an AI-powered preventive healthcare platform for India.

## Run locally

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000.

## Checks

```bash
npm run lint
npx tsc --noEmit
```

## Deploy on Vercel

1. Import this repository in Vercel.
2. Set the root directory to `web`.
3. Framework preset: Next.js. Build command: `npm run build`.
4. Deploy. The site includes `sitemap.xml`, `robots.txt`, and Open Graph metadata.

The demo gauge and email form are illustrative. Submitting the form confirms on the page and does not send mail yet.
