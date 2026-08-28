---
kind: frontend_style
name: Tailwind CSS Design System with Custom Brand Tokens and Vue Component Styling
category: frontend_style
scope:
    - '**'
source_files:
    - travel-recovery-os/frontend/tailwind.config.js
    - travel-recovery-os/frontend/src/assets/main.css
    - travel-recovery-os/frontend/postcss.config.js
    - travel-recovery-os/frontend/package.json
    - travel-recovery-os/frontend/src/components/Navbar.vue
    - travel-recovery-os/frontend/src/components/LiveTerminal.vue
---

## What system/approach is used

The frontend (`travel-recovery-os/frontend`) uses **Vue 3 + Vite** styled entirely with **Tailwind CSS v3.4**. There is no component UI library (e.g., shadcn, AntD); all visual styling is built from Tailwind utility classes augmented by a custom design token set defined in `tailwind.config.js`. PostCSS with Autoprefixer processes the styles, and the single global stylesheet lives at `src/assets/main.css`.

## Key files and packages

- `frontend/tailwind.config.js` — central design-token source: brand palette, warm neutrals, status colors, fonts, radii, shadows, gradients, animations/keyframes.
- `frontend/src/assets/main.css` — global base styles via `@tailwind base/components/utilities`, plus reusable `.ops-card`, `.text-gradient-brand`, `.bg-brand-gradient`, shimmer/entrance animations, boarding-pass perforated edge, scanline terminal overlay, custom scrollbars, selection color, and mobile/touch responsive overrides.
- `frontend/postcss.config.js` — enables `tailwindcss` and `autoprefixer` plugins.
- `frontend/package.json` — declares `vue 3.4`, `tailwindcss 3.4`, `vite 5`, `@vitejs/plugin-vue`, `lucide-vue-next` icons, `@vueuse/core`; no other UI framework dependency.
- `frontend/index.html` — root HTML loaded by Vite.
- `frontend/src/components/*.vue` — components compose Tailwind utilities directly; no `<style>` blocks are needed because tokens and utilities cover everything.

## Architecture and conventions

### Design tokens (single source of truth)
All colors, fonts, radii, shadows, gradients, and animations are declared once under `theme.extend`:
- **Brand palette**: `brand.purple (#8A4FFF)`, `brand.blue`, `brand.cyan`, `brand.lavender` (+ `-light` variants).
- **Warm neutrals**: `warm.50–900` replacing cold slate tones for a warmer feel.
- **Semantic status colors**: `success`, `warning`, `danger`, `info` each with `light`/`DEFAULT`/`dark` shades.
- **Typography**: `font-display` (Outfit → Inter → system-ui), `font-sans` (Inter), `font-mono` (Fira Code/JetBrains Mono).
- **Shadows**: `soft`, `soft-md`, `soft-lg`, `glow-purple`, `glow-blue`, `inner-soft`.
- **Gradients**: `brand-gradient`, `brand-gradient-soft`, `warm-gradient`.
- **Animations**: `ping-slow`, `pulse-soft`, `slide-up`, `slide-in-right`, `fade-in`, `shimmer`, `float`, `bounce-gentle`, `gradient-x`.

Components reference these tokens exclusively (e.g., `bg-brand-gradient`, `shadow-soft`, `text-warm-900`, `border-warm-200`, `animate-fade-in`).

### Global reusable CSS classes
`main.css` defines application-wide class names that encapsulate multi-property patterns:
- `.ops-card` / `.ops-card-nested` — card surface with border, radius, shadow, hover lift.
- `.text-gradient-brand` / `.bg-brand-gradient` — gradient text/background.
- `.animate-shimmer`, `.animate-slide-up`, `.animate-fade-in`, `.animate-float`, `.animate-pulse-ring` — animation classes.
- `.boarding-pass-edge` — decorative perforated edges using pseudo-elements.
- `.scanline-overlay` — subtle CRT-style scanlines for terminal-like surfaces.
- Custom `::-webkit-scrollbar` and `::selection` styles.

These are applied as plain class names alongside Tailwind utilities in Vue templates.

### Responsive strategy
- Mobile-first Tailwind breakpoints (`sm:`, `md:`, `lg:`) are used throughout components (e.g., Navbar, LiveTerminal) to progressively enhance layout.
- A `@media (max-width: 640px)` block in `main.css` adjusts boarding-pass cutouts, disables hover transforms on touch devices, tightens card radii, and prevents horizontal overflow.
- A `@media (hover: none) and (pointer: coarse)` block specifically disables hover effects that don't work on touch devices.

### Animation conventions
- Entrance animations use `animate-fade-in` and `animate-slide-up`.
- Status indicators use `animate-ping` combined with small colored dots.
- Shimmer loading uses the `shimmer` keyframe.
- Floating/gentle bounce effects are available via `animate-float` and `animate-bounce-gentle`.

### Iconography
Icons come from `lucide-vue-next` (imported where needed) and inline SVGs; emoji characters are also used decoratively inside components (e.g., `📡`, `🎟️`, `⚠️`).

### Build pipeline
Vite builds the Vue app; PostCSS runs Tailwind then Autoprefixer. The content glob `./src/**/*.{vue,js,ts,jsx,tsx}` ensures all component files are scanned for utility usage so unused CSS is tree-shaken.

## Conventions and constraints observed

- **No scoped `<style>` blocks in components** — components rely entirely on Tailwind utilities and the shared classes in `main.css`, keeping styling centralized.
- **Colors are never hardcoded hex literals in components** — they go through the `brand.*`, `warm.*`, `success/warning/danger/info.*` tokens defined in `tailwind.config.js`.
- **Cards always use `.ops-card`** rather than redefining background/border/shadow per component.
- **Gradients are referenced via `bg-brand-gradient` or the Tailwind `backgroundImage` token**, not raw `linear-gradient(...)` in components.
- **Fonts are selected via `font-display`, `font-sans`, `font-mono`** tokens instead of direct font-family strings.
- **Responsive behavior is expressed with Tailwind's `sm:`/`md:`/`lg:` prefixes**; global media queries in `main.css` only handle cross-cutting concerns like scrollbar styling and touch-device fallbacks.
- **Animations are consumed as `animate-*` classes** generated from the keyframes in `tailwind.config.js` (with duplicate definitions in `main.css` for legacy compatibility).
- **Dark/terminal surfaces** use the dark end of the warm scale (`bg-warm-900`, `border-warm-700`, `text-warm-300`) paired with the `.scanline-overlay` class for the terminal view.