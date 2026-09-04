# WeatherGPT — Persistent Project Context

> This file is the persistent memory/context document for the WeatherGPT SIH project.
> Keep it inside the project root and update it after meaningful development sessions.
> It works together with `WeatherGPT_SIH_Frontend_Master_Prompt.txt`.

---

## 1. PROJECT IDENTITY

**Project:** WeatherGPT  
**Purpose:** AI-powered weather intelligence platform for Smart India Hackathon (SIH).

WeatherGPT is intended to combine real-time weather information with an AI assistant that can explain weather naturally, support multilingual interaction, provide voice interaction, surface alerts, visualize weather data, and help users make practical decisions.

The product should feel like a polished real product, not a basic weather dashboard or a chatbot placed beside weather cards.

### Core product idea

> "WeatherGPT understands the weather, explains it naturally, speaks your language, and helps you make decisions."

---

# 2. MASTER FRONTEND SPECIFICATION

The detailed frontend specification is stored in:

`WeatherGPT_SIH_Frontend_Master_Prompt.txt`

### IMPORTANT

Before making major frontend changes:

1. Read this file.
2. Read the current project structure.
3. Read this `PROJECT_CONTEXT.md`.
4. Inspect existing implementations before creating new ones.
5. Preserve working functionality.
6. Do not rewrite working components unnecessarily.
7. Continue from the current project state rather than starting over.

---

# 3. DEVELOPMENT PRINCIPLES

The application must prioritize:

1. Functionality
2. Correct architecture
3. Responsive design
4. Accessibility
5. Backend integration
6. Visual polish
7. Advanced 3D/liquid effects
8. Performance optimization

Advanced visual effects must never be allowed to break the core product.

The application should remain useful even if:
- WebGL is unavailable.
- Animations are disabled.
- Network is slow.
- Some APIs fail.
- Voice is unavailable.
- Location permission is denied.

---

# 4. TARGET FRONTEND STACK

Preferred technologies:

- React
- TypeScript
- Vite
- React Router
- Tailwind CSS or equivalent maintainable styling system
- Framer Motion or equivalent animation system
- React Three Fiber / Three.js where useful
- Recharts or equivalent chart library
- Fetch/Axios through a centralized API layer

Use TypeScript strictly.

Do not add dependencies without a reason.

---

# 5. EXPECTED PROJECT STRUCTURE

Recommended structure:

```text
WeatherGPT/
│
├── FRONTEND_MASTER_PROMPT.txt
├── PROJECT_CONTEXT.md
├── README.md
├── package.json
│
├── public/
│
└── src/
    ├── app/
    ├── assets/
    ├── components/
    │   ├── common/
    │   ├── navigation/
    │   ├── weather/
    │   ├── forecast/
    │   ├── alerts/
    │   ├── maps/
    │   ├── chat/
    │   ├── voice/
    │   ├── charts/
    │   └── 3d/
    │
    ├── pages/
    ├── layouts/
    ├── hooks/
    ├── services/
    │   ├── api/
    │   ├── weather/
    │   ├── ai/
    │   ├── voice/
    │   └── location/
    │
    ├── store/
    ├── types/
    ├── utils/
    ├── constants/
    └── styles/
```

The exact structure can evolve if there is a better architectural reason.

---

# 6. MAIN APPLICATION AREAS

The planned application contains:

- Dashboard
- Weather details
- Hourly forecast
- Daily forecast
- Weather map
- Weather alerts
- WeatherGPT AI assistant
- Voice assistant
- Multilingual interface
- Location search/current location
- Settings/preferences

Potential navigation:

```text
HOME / DASHBOARD
WEATHER
FORECAST
MAP
ALERTS
WEATHERGPT
VOICE
SETTINGS
```

Not every feature has to be a completely separate route if a combined experience is more usable.

---

# 7. FRONTEND FEATURE CHECKLIST

## Core Weather

- [ ] Current weather
- [ ] Temperature
- [ ] Feels-like temperature
- [ ] Weather condition
- [ ] High/low
- [ ] Humidity
- [ ] Wind
- [ ] Visibility
- [ ] Pressure
- [ ] UV
- [ ] Sunrise/sunset
- [ ] Cloud cover
- [ ] Precipitation probability
- [ ] Air quality if supplied by backend

## Forecast

- [ ] Hourly forecast
- [ ] Daily forecast
- [ ] Expandable forecast details
- [ ] Temperature trend
- [ ] Rain probability
- [ ] Wind information
- [ ] Forecast charts

## AI

- [ ] WeatherGPT chat
- [ ] User messages
- [ ] AI messages
- [ ] Loading/typing state
- [ ] Streaming support if backend supports it
- [ ] Retry failed response
- [ ] Copy response
- [ ] Clear conversation
- [ ] Suggested questions
- [ ] Weather-aware context
- [ ] Location-aware context

## Voice

- [ ] Microphone UI
- [ ] Permission handling
- [ ] Listening state
- [ ] Processing state
- [ ] Responding state
- [ ] Stop action
- [ ] Transcript
- [ ] Speech output
- [ ] Error state
- [ ] Animated voice orb/waveform

## Languages

Architecture should support:

- [ ] English
- [ ] Hindi
- [ ] Gujarati
- [ ] Additional Indian languages later

Do not hard-code user-facing strings inside components.

## Location

- [ ] Browser geolocation
- [ ] Manual location search
- [ ] Autocomplete if supported
- [ ] Current location
- [ ] Recent locations
- [ ] Saved locations
- [ ] Permission-denied state
- [ ] Location error state

## Alerts

- [ ] Alert banner
- [ ] Alert list
- [ ] Alert detail
- [ ] Severity
- [ ] Affected area
- [ ] Issue time
- [ ] Expiry
- [ ] Recommended action

## Map

- [ ] Current location
- [ ] Zoom
- [ ] Map layer controls
- [ ] Temperature layer if available
- [ ] Precipitation layer if available
- [ ] Wind layer if available
- [ ] Cloud layer if available
- [ ] Alerts layer if available
- [ ] Legend

---

# 8. VISUAL DESIGN DIRECTION

The interface should feel:

- Futuristic
- Premium
- Intelligent
- Atmospheric
- Modern
- Trustworthy
- Interactive
- Fast
- SIH-ready

Avoid making it look like:
- A generic admin dashboard
- A crypto dashboard
- A gaming website
- A copied UI template

---

# 9. ADVANCED UI EFFECTS

Planned visual effects include:

## 3D

Use selectively:

- 3D weather orb
- Interactive globe
- Atmospheric visualization
- 3D weather illustrations
- Depth-based cards
- Interactive location marker

Possible interactions:
- Pointer-based tilt
- Parallax
- Soft elevation
- Cursor-following highlights
- Smooth spring animations

Every important 3D feature needs a fallback.

---

## Liquid / Glass UI

Use:

- Glass cards
- Frosted panels
- Liquid-style backgrounds
- Soft gradient blobs
- Atmospheric layers
- Refraction-like highlights
- Glass buttons

Do not blur everything.

Content must remain readable.

---

## Weather-Reactive Environment

The interface can react to weather:

### Clear
- Open sky atmosphere
- Soft particles
- Bright gradients

### Cloudy
- Layered cloud visuals
- Muted atmosphere

### Rain
- Subtle rain
- Liquid/glass atmosphere

### Storm
- Darker atmosphere
- Restrained lightning effect

### Night
- Stars
- Dark sky
- Soft ambient particles

Effects must not interfere with information.

---

# 10. NAVIGATION RULES

Navigation must always feel predictable.

Create reusable:

`BackButton`

Requirements:

- Use browser/router history when appropriate.
- Fall back to a safe parent/home route if necessary.
- Work with keyboard.
- Have visible hover/focus states.
- Work properly on mobile.
- Do not trap users inside detail pages.

The user should always know:
- Where they are.
- How to go back.
- How to return to the dashboard.

---

# 11. RESPONSIVE DESIGN

The application must support:

- Small phones
- Large phones
- Tablets
- Laptops
- Desktop
- Large displays

Mobile requirements:

- No horizontal overflow.
- Touch-friendly controls.
- Compact navigation.
- Horizontal forecast scrolling where useful.
- Readable charts.
- Simplified 3D effects where necessary.

Desktop can use:
- Larger hero section
- Expanded navigation
- Multi-column dashboard
- Richer visualizations
- More detailed 3D effects

---

# 12. ACCESSIBILITY

Must include:

- Semantic HTML
- Keyboard navigation
- Visible focus indicators
- Accessible labels
- Good contrast
- Screen-reader-friendly content
- Text summaries for charts
- Color-independent alert severity
- Reduced-motion support

When `prefers-reduced-motion` is active:

- Reduce parallax.
- Disable unnecessary 3D movement.
- Reduce particle animation.
- Prefer simple fades.

---

# 13. STATE MANAGEMENT

Keep these categories separate:

### Server state
Weather, forecast, alerts, map data, AI responses.

### UI state
Open menus, active tabs, dialogs, animations.

### User preferences
Language, units, theme, reduced motion, saved location.

### Chat state
Messages, loading, errors, current conversation.

Do not make everything global.

---

# 14. API ARCHITECTURE

Never put raw API calls throughout UI components.

Use centralized services.

Conceptual services:

```text
weatherService
forecastService
locationService
alertService
aiService
voiceService
```

Use typed interfaces such as:

```text
WeatherData
ForecastData
HourlyForecast
DailyForecast
WeatherAlert
AIMessage
VoiceRequest
VoiceResponse
LocationResult
```

Do not invent endpoint names if backend implementation has not finalized them.

When the backend is connected, adapt the service layer rather than rewriting the UI.

---

# 15. BACKEND INTEGRATION PRINCIPLE

The frontend should conceptually follow:

```text
USER
  ↓
REACT UI
  ↓
SERVICE / API LAYER
  ↓
BACKEND
  ↓
WEATHER / AI / VOICE / LOCATION SERVICES
  ↓
NORMALIZED RESPONSE
  ↓
FRONTEND STATE
  ↓
UI
```

The UI must not depend directly on a specific third-party weather provider.

---

# 16. LOADING / ERROR / EMPTY STATES

Every major data-driven component needs states for:

```text
IDLE
LOADING
SUCCESS
EMPTY
ERROR
```

Examples:

- Weather unavailable
- Forecast unavailable
- AI unavailable
- Voice permission denied
- Network disconnected
- Location unavailable
- Map failed
- Search returned no results

Errors should explain:

1. What happened.
2. What the user can do.
3. Whether retry is possible.

---

# 17. PERFORMANCE RULES

Advanced UI must not destroy performance.

Use:

- Lazy-loaded routes
- Lazy-loaded 3D
- Lazy-loaded maps
- Code splitting
- Optimized assets
- Debounced search
- Minimal unnecessary rerenders
- Paused offscreen animations
- Lightweight effects

The dashboard should become usable before all decorative effects finish loading.

---

# 18. SECURITY RULES

Never:

- Expose secret API keys.
- Put private credentials in frontend code.
- Trust client-side authorization.
- Render unsafe AI HTML.
- Log sensitive information.

AI output must be rendered safely.

---

# 19. DEVELOPMENT PHASES

## PHASE 1 — FOUNDATION

Status: NOT STARTED / IN PROGRESS / COMPLETE

Tasks:
- React + TypeScript setup
- Routing
- Global styles
- Design tokens
- App shell
- Navigation
- Responsive foundation
- Reusable UI primitives

---

## PHASE 2 — CORE WEATHER

Tasks:
- Current weather
- Location
- Weather cards
- Metrics
- Hourly forecast
- Daily forecast
- Loading states
- Error states

---

## PHASE 3 — VISUALIZATION

Tasks:
- Weather charts
- Weather-reactive backgrounds
- Weather atmosphere
- Map
- Map controls

---

## PHASE 4 — WEATHERGPT

Tasks:
- Chat UI
- AI service layer
- Message states
- Suggested prompts
- Retry
- Copy
- AI insight cards

---

## PHASE 5 — VOICE

Tasks:
- Microphone interface
- Listening animation
- Processing animation
- Speech input
- AI response
- Speech output
- Voice errors

---

## PHASE 6 — MULTILINGUAL

Tasks:
- i18n architecture
- Language selector
- English
- Hindi
- Gujarati
- Voice language selection
- Translation fallback

---

## PHASE 7 — ADVANCED UI

Tasks:
- 3D hero
- Interactive 3D elements
- Liquid glass
- Advanced hover effects
- Atmospheric effects
- Page transitions
- Micro-interactions

---

## PHASE 8 — FINAL SIH POLISH

Tasks:
- Accessibility audit
- Responsive audit
- Performance audit
- Error handling
- Browser testing
- Mobile testing
- Demo flow
- Visual consistency
- Remove console errors
- Remove dead code

---

# 20. CURRENT PROGRESS TRACKER

Update this section after every meaningful session.

## Overall

- [ ] Project initialized
- [ ] Architecture established
- [ ] Design system established
- [ ] Navigation complete
- [ ] Dashboard complete
- [ ] Weather integration complete
- [ ] Forecast complete
- [ ] Charts complete
- [ ] Map complete
- [ ] Alerts complete
- [ ] AI chat complete
- [ ] Voice complete
- [ ] Multilingual support complete
- [ ] 3D UI complete
- [ ] Liquid UI complete
- [ ] Responsive optimization complete
- [ ] Accessibility complete
- [ ] Performance optimization complete
- [ ] SIH demo polish complete

---

# 21. CURRENT SESSION STATUS

Fill this in after each development session.

### Date
`YYYY-MM-DD`

### Current Phase
`Example: PHASE 2 — CORE WEATHER`

### What was completed
```text
- 
- 
- 
```

### What is currently being worked on
```text
- 
```

### What remains
```text
- 
- 
- 
```

### Files/components changed
```text
- 
- 
```

### Known bugs
```text
- None
```

### Important decisions made
```text
- 
```

### Next task
```text
- 
```

---

# 22. DECISION LOG

Record architectural decisions here.

## Decision 001
**Topic:** Frontend architecture  
**Decision:** Use modular React + TypeScript architecture with centralized services.  
**Reason:** Keeps UI independent from backend/provider implementation.

## Decision 002
**Topic:** Advanced visuals  
**Decision:** 3D/liquid effects are progressive enhancements.  
**Reason:** Core weather functionality must remain reliable and performant.

## Decision 003
**Topic:** API integration  
**Decision:** Components should communicate with typed service modules rather than raw API requests.  
**Reason:** Makes backend changes easier and keeps UI maintainable.

Add future decisions below.

---

# 23. AI CODING AGENT RULES

When using Cursor, Claude Code, or another coding agent:

## Before coding

Read:

```text
FRONTEND_MASTER_PROMPT.txt
PROJECT_CONTEXT.md
```

Then inspect:

```text
src/
package.json
existing routes
existing services
existing components
```

## Never do this

- Do not delete working functionality just to simplify implementation.
- Do not rebuild the entire project unnecessarily.
- Do not create duplicate components when an existing component can be extended.
- Do not invent backend APIs.
- Do not hard-code secrets.
- Do not add unnecessary libraries.
- Do not replace the design system without a clear reason.
- Do not remove accessibility features.
- Do not remove responsive behavior.
- Do not implement fake production functionality.

## Before finishing a task

Check:

```text
- TypeScript errors
- Runtime errors
- Console errors
- Broken imports
- Responsive layout
- Existing functionality
- Loading state
- Error state
- Accessibility
```

Then update this file.

---

# 24. SESSION RESUME PROMPT FOR CURSOR

Use this whenever starting a new development session:

```text
You are continuing development of the WeatherGPT SIH frontend.

First read:
1. FRONTEND_MASTER_PROMPT.txt
2. PROJECT_CONTEXT.md

Then inspect the existing project and determine the current implementation state.

Do NOT restart the project.

Do NOT rewrite working code unnecessarily.

Preserve existing functionality and architecture.

Identify:
- What has already been implemented.
- What is incomplete.
- What the current phase is.
- What the next logical task is.

Before coding, briefly state your understanding of the current state and the task you will implement.

Then implement only the required next task.

Follow the design system and frontend master prompt.

Keep the UI responsive, accessible, performant, and backend-ready.

Do not invent backend endpoint contracts.

After implementation:
1. Check for TypeScript errors.
2. Check imports.
3. Check runtime issues.
4. Check responsive behavior.
5. Check that existing features still work.
6. Update PROJECT_CONTEXT.md with:
   - completed work
   - files changed
   - remaining work
   - known issues
   - next task
   - important decisions
```

---

# 25. TASK EXECUTION PROMPT

For individual features, use:

```text
Implement the next unfinished task from PROJECT_CONTEXT.md.

Before changing code:
- Read FRONTEND_MASTER_PROMPT.txt.
- Read PROJECT_CONTEXT.md.
- Inspect related existing components.
- Reuse existing components where possible.

Implement the feature completely.

Include:
- responsive behavior
- loading state
- error state where applicable
- empty state where applicable
- keyboard accessibility
- appropriate animations
- proper TypeScript types

Do not invent backend endpoints.

If backend integration is not ready, create a clean service abstraction/interface rather than hard-coding fake production behavior.

Do not modify unrelated features.

After completion, verify the implementation and update PROJECT_CONTEXT.md.
```

---

# 26. VISUAL QUALITY CHECKLIST

Before declaring a UI section complete:

### Layout
- [ ] Good spacing
- [ ] Clear hierarchy
- [ ] Responsive
- [ ] No overflow

### Typography
- [ ] Readable
- [ ] Clear headings
- [ ] Proper contrast
- [ ] Mobile-safe sizing

### Components
- [ ] Consistent radius
- [ ] Consistent spacing
- [ ] Consistent borders
- [ ] Consistent shadows/glows

### Interaction
- [ ] Hover
- [ ] Focus
- [ ] Active
- [ ] Disabled
- [ ] Loading

### Motion
- [ ] Smooth
- [ ] Short
- [ ] Purposeful
- [ ] Reduced-motion compatible

### Accessibility
- [ ] Keyboard usable
- [ ] Screen-reader labels
- [ ] Color not the only indicator
- [ ] Good contrast

---

# 27. SIH DEMO FLOW

The application should support a compelling live demonstration.

Recommended flow:

```text
1. Open Dashboard
        ↓
2. Show current weather
        ↓
3. Show forecast/trends
        ↓
4. Demonstrate weather alert
        ↓
5. Ask WeatherGPT a natural-language question
        ↓
6. Demonstrate voice interaction
        ↓
7. Switch language
        ↓
8. Show weather/map visualization
        ↓
9. Demonstrate responsive/mobile experience
```

The demo should show that WeatherGPT is more than a normal weather application.

---

# 28. QUALITY BAR

The project is not complete merely because all pages exist.

A feature is considered complete when:

- It works.
- It is responsive.
- It handles loading.
- It handles failure.
- It is accessible.
- It integrates cleanly with architecture.
- It does not break existing functionality.
- It matches the design system.
- It performs acceptably.

---

# 29. CURRENT NEXT TASK

This is the single most important section for continuing work.

```text
NEXT TASK:
[Write the next concrete implementation task here]

Example:
"Build the responsive WeatherGPT dashboard shell with navbar, mobile navigation,
weather hero, quick metric cards, hourly forecast section, and reusable glass card system."
```

Only keep ONE primary next task here.

---

# 30. END-OF-SESSION CHECKLIST

Before stopping work for the day:

- [ ] Save all files.
- [ ] Test the current implementation.
- [ ] Check console.
- [ ] Check TypeScript/build.
- [ ] Record completed tasks.
- [ ] Record incomplete tasks.
- [ ] Record bugs.
- [ ] Record architectural decisions.
- [ ] Update NEXT TASK.
- [ ] Update CURRENT SESSION STATUS.
- [ ] Update feature checkboxes.

This makes the project easy to continue tomorrow, next week, or later.

---

# 31. GOLDEN RULE

Never optimize the project for "how much code was generated."

Optimize for:

```text
QUALITY
+
RELIABILITY
+
MAINTAINABILITY
+
USER EXPERIENCE
+
SIH DEMO IMPACT
```

WeatherGPT should ultimately feel like a cohesive AI weather product with a premium interface, not a collection of AI-generated components.
