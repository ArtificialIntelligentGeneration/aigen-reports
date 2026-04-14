# AiGen Reports

> Read-only utility that pulls TikTok Ads campaign metrics (spend, clicks,
> impressions, conversions) from authorized advertiser accounts via the
> official Marketing API. Exports to CSV and Google Sheets.

```
$ aigen-reports pull --advertiser 7xxxxxxxxxx --metric spend,clicks,conversions \
                     --range last-7d --out ./report.csv
✓ authorized as: my-tiktok-ads-account
✓ pulled 7 days × 14 campaigns × 4 metrics  →  report.csv (12 KB)
```

## What it does

- Authorizes against your own TikTok Ads account via the official
  TikTok for Business OAuth flow (Reporting permission category only).
- Pulls aggregated campaign / ad group / ad performance metrics.
- Writes the result to a CSV file, a Google Sheets tab, or an HTTPS
  webhook of your choice.
- That's it. No dashboard, no SaaS, no minimum spend, no telemetry.

## What it does NOT do

- Manage campaigns, ad groups, ads, audiences, or creatives. (No write
  scopes are requested.)
- Touch TikTok consumer-side data (videos, comments, user profiles).
- Phone home. The tool runs locally; the only outbound call is to
  `business-api.tiktok.com`.

## Install

```
pip install aigen-reports
```

Or clone and run from source:

```
git clone https://github.com/ArtificialIntelligentGeneration/aigen-reports.git
cd aigen-reports
pip install -e .
```

## First-time setup

1. Create a TikTok Marketing API app at <https://business-api.tiktok.com/portal/>.
2. In the app, request the **Reporting** permission category.
3. Set the redirect URI to `http://localhost:8765/callback` (or your own).
4. Copy `App ID` and `Secret` into a local `.env`:

   ```
   TIKTOK_APP_ID=...
   TIKTOK_APP_SECRET=...
   TIKTOK_REDIRECT_URI=http://localhost:8765/callback
   ```

5. Run the auth flow once:

   ```
   aigen-reports auth
   ```

   The browser opens, you authorize, the tool stores the access token
   encrypted in `~/.aigen-reports/credentials.json`.

## Usage

```
aigen-reports pull \
  --advertiser <ADVERTISER_ID> \
  --metric spend,clicks,impressions,conversions \
  --breakdown campaign \
  --range last-7d \
  --out ./report.csv
```

Output destinations:

- `--out report.csv` → CSV
- `--out gsheet:1AbC...` → append to a Google Sheets tab
- `--out https://example.com/hook` → POST JSON to a webhook

## Configuration file

You can save report definitions to `~/.aigen-reports/reports.yaml`:

```yaml
- name: weekly-evergreen
  advertiser: '7xxxxxxxxxx'
  metric: [spend, clicks, conversions]
  breakdown: campaign
  range: last-7d
  out: 'gsheet:1AbC...'
```

Then run with:

```
aigen-reports run weekly-evergreen
```

## Scheduling

The tool intentionally does not include a built-in scheduler — use
whatever your environment already has (`cron`, `launchd`, GitHub
Actions, etc.). One example is included in `examples/cron.txt`.

## License

MIT. See [LICENSE](./LICENSE).

## Author

Built by [Julian Reiter](mailto:julian@aigen-agency.com). The tool is
released as open source because the underlying chore (manually
exporting CSVs from the TikTok Ads Manager UI) is universal among ad
operators. Bug reports and pull requests welcome.
