# AI Tools Momentum Index

Which tools on the [Awesome AI Marketing](../README.md) list are gaining attention, and which are cooling off. Rebuilt automatically every Monday by [a GitHub Action](../.github/workflows/momentum.yml); nobody edits these numbers by hand.

**Last updated:** 26 November 2026

**This month's biggest mover:** Perplexity (+126%). **Cooling off most:** Google Analytics (-18%).

![Momentum chart](chart.svg)

| Rank | Tool | Momentum | Wikipedia views (28 days) | Change | HN mentions (28 days) | Change | GitHub stars | Stars gained (28 days) |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Perplexity | **+126%** | 57,208 | -5% | 239 | +257% | – | – |
| 2 | Mailchimp | **+120%** | 7,210 | +119% | 37 | +121% | – | – |
| 3 | PostHog † | **+29%** | – | – | 38 | +29% | 41,163 | – |
| 4 | Claude | **+20%** | 189,634 | +11% | 7,890 | +28% | – | – |
| 5 | Notion | **+19%** | 10,515 | -12% | 106 | +51% | – | – |
| 6 | Astro † | **+17%** | – | – | 9 | +17% | 64,231 | – |
| 7 | Canva | **+14%** | 85,278 | +1% | 54 | +27% | – | – |
| 8 | Grammarly | **+11%** | 9,147 | -10% | 20 | +32% | – | – |
| 9 | CapCut | **+10%** | 26,536 | +24% | 1 | -4% | – | – |
| 10 | Figma | **+9%** | 17,032 | -10% | 162 | +29% | – | – |
| 11 | Gemini | **+7%** | 66,914 | -14% | 1,503 | +28% | – | – |
| 12 | Model Context Protocol | **+6%** | 34,995 | -2% | 14 | +15% | 92,278 | – |
| 13 | Zapier | **+6%** | 3,267 | -12% | 13 | +23% | – | – |
| 14 | Adobe Firefly | **+5%** | 2,115 | -2% | 4 | +12% | – | – |
| 15 | Semrush | **+4%** | 3,153 | -11% | 5 | +20% | – | – |
| 16 | HeyGen | **+4%** | 2,256 | -0% | 3 | +8% | – | – |
| 17 | Ahrefs † | **+4%** | – | – | 3 | +4% | – | – |
| 18 | Vercel | **+2%** | 12,981 | -7% | 316 | +11% | – | – |
| 19 | n8n | **+1%** | 9,550 | -0% | 41 | +3% | 212,277 | – |
| 20 | ElevenLabs | **+1%** | 29,143 | -7% | 43 | +10% | – | – |
| 21 | Listmonk † | **+0%** | – | – | 0 | +0% | 24,474 | – |
| 22 | Evidence † | **+0%** | – | – | 0 | +0% | 7,148 | – |
| 23 | GrowthBook † | **+0%** | – | – | 1 | +0% | 8,662 | – |
| 24 | NotebookLM | **-0%** | 9,307 | -17% | 10 | +17% | – | – |
| 25 | Descript † | **-3%** | – | – | 3 | -3% | – | – |
| 26 | Midjourney | **-4%** | 12,890 | -8% | 18 | +0% | – | – |
| 27 | Runway | **-6%** | 3,767 | -12% | 1 | +0% | – | – |
| 28 | Ghost | **-6%** | 1,295 | +1% | 0 | -14% | 55,928 | – |
| 29 | Umami † | **-7%** | – | – | 1 | -7% | 40,395 | – |
| 30 | ChatGPT | **-12%** | 1,745,488 | -21% | 1,382 | -2% | – | – |
| 31 | Streamlit † | **-13%** | – | – | 2 | -13% | 46,515 | – |
| 32 | Google Analytics | **-18%** | 3,097 | -20% | 13 | -16% | – | – |

† One signal only (no Wikipedia article), so treat the score with more caution.

## How the score works

For each tool, every available signal compares the last 28 days with the 28 days before:

- **Wikipedia views**: daily page views of the tool's English Wikipedia article, excluding bots ([Wikimedia API](https://wikimedia.org/api/rest_v1/)).
- **Hacker News mentions**: stories and comments matching the tool's name ([HN Algolia API](https://hn.algolia.com/api)). A rough signal of builder interest.
- **GitHub stars**: shown for open-source tools as context, not scored. Stars gained appears once the index has 4 weeks of its own history.

Small numbers are damped (adding 500 views and 25 mentions to both windows) so a jump from 3 to 9 doesn't read as +200%. **Momentum** is the average change across the Wikipedia and Hacker News signals a tool has. It measures attention, not quality: a tool can trend because of bad news too.

Raw weekly numbers live in [data/history.csv](data/history.csv), so anyone can check or reuse them. The code is [momentum.py](momentum.py), standard-library Python with no keys.

## Run it yourself

```bash
python3 momentum/momentum.py
```

Add or change tools in [tools.json](tools.json).

## Data gaps this week

- Ahrefs: no wikipedia data for `Ahrefs`
