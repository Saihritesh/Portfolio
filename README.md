# Knight for Hire

*A Knight hath Risen.*

The portfolio of **Saihritesh Kowtarapu**, AI/ML engineer, built as a pixel-art castle you explore as a knight.
Press start, walk the halls, and every room holds part of the story:

| Room | What's inside |
|---|---|
| Chronicle Hall | Welcome signpost and experience |
| Library | Education and the resume (viewable in-page) |
| Treasury | Projects, with links to code and live demos |
| Armory | Skills |
| Trophy Room | Certifications and honours |
| Throne Room | Contact form that delivers straight to my inbox |
| Gate Hall | Strike the lever, open the portcullis, and defend the courtyard in a five-wave siege with a boss fight |

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build in dist/
```

Controls: arrow keys or A/D to move, Space to jump, X to slash, E to interact, M for the map. Touch controls appear on phones.

## How it's built

- **Vite + vanilla JavaScript**, no framework. The game loop, rooms, pop-ups and the courtyard mini-game live in `src/`.
- **All portfolio text** is in `src/content.json`: rooms, objects, pop-ups, links and the map.
- **Pixel art** is generated procedurally with Python and Pillow (`tools/`), rendered at native resolution and scaled with nearest-neighbour for crisp pixels. Pristine room paintings live in `tools/rooms_base/`, and each script rebuilds its room from them.
- **Contact form** posts to a form relay (`person.contact_endpoint` in `content.json`).

## Deploy

Any static host works. On Vercel or Netlify, import the repo and use the defaults: build command `npm run build`, output directory `dist`.
