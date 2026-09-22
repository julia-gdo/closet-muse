# Closet Muse

Style your real wardrobe.

Closet Muse recreates outfits people save on Pinterest and Instagram —
using clothes they already own. Upload your closet, upload your
inspiration, and AI generates outfits from what you actually have. No
shopping links, no AI-generated clothing — just your real wardrobe,
styled by AI.

**Status: MVP in active development**

## Why I built this

People save outfit inspiration constantly and rarely recreate it —
they forget what they own, don't know how to style pieces together,
or assume the look requires buying something new. Existing wardrobe
apps focus on inventory, not on the actual styling problem. This
project is my attempt to close that gap.

## Technical highlights

- **Auth & security:** Supabase-based authentication with JWT
  validation on the backend against Supabase's public key — no
  passwords or tokens handled or stored by my own server
- **Async processing:** clothing and inspiration image uploads are
  handled by a background job worker with automatic retry on failure,
  rather than blocking the request
- **AI pipeline:** two separate AI stages — one for tagging uploaded
  clothing (type, color, style) after automatic background removal,
  and a second for analyzing inspiration images into style tags and a
  summary
- **Deliberate scope decisions:** clothing artwork is hand-illustrated
  rather than AI-generated, to keep the product cost-sustainable as a
  solo project; outfit *matching* is AI-driven, outfit *art* is not —
  a decision made explicitly to control recurring API costs

## Tech stack

**Frontend:** Next.js, TypeScript, Tailwind CSS
**Backend:** Python
**Auth & Database:** Supabase (Postgres, JWT auth)
**Infra:** background job worker with retry logic

## Features

| Status | Feature |
|---|---|
| ✅ | Supabase auth (sign up, login, JWT validation) |
| ✅ | Clothing upload with automatic background removal |
| ✅ | AI tagging of clothing items (type, color, style) |
| ✅ | Closet view with filters and live status |
| ✅ | Inspiration image analysis (backend) |
| ✅ | Background job worker with retry |
| 🔄 | Outfit generation engine |
| 🔄 | Outfit display and saving |
| 📋 | "Dress me like this" — recreate a single inspiration outfit in one tap |

## Running locally

_(add install + run steps once finalized)_

## About this project

Built solo as a portfolio project, using AI-assisted development
throughout. I'm the sole architect of the product and technical
decisions — including the auth approach, background job design, and
the AI/hand-drawn asset scope tradeoff described above.
