# WeatherGPT — Frontend Development Roadmap

## Purpose

This roadmap is the execution plan for building the complete WeatherGPT frontend before real backend integration.

The frontend will be developed with React + TypeScript + Vite and will use mock services/data behind a service abstraction. Later, the mock implementation can be replaced with the real backend without rewriting the UI.

The three major frontend phases are:

1. Foundation & UI System
2. Weather Experience
3. AI & Advanced Features

Three Cursor agents can work in parallel, but each agent must have clearly separated ownership to minimize merge conflicts.

---

# 1. Frontend Architecture

Target structure:

```text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── providers/
│   │   └── router/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── shared/
│   ├── features/
│   │   ├── weather/
│   │   ├── forecast/
│   │   ├── alerts/
│   │   ├── maps/
│   │   ├── location/
│   │   ├── ai/
│   │   ├── chat/
│   │   ├── voice/
│   │   └── i18n/
│   ├── pages/
│   ├── services/
│   │   ├── api/
│   │   └── mock/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── config/
│   ├── assets/
│   └── styles/
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

The exact structure may evolve if a better technical structure is discovered, but shared UI, feature modules, services, types, and configuration must remain clearly separated.

---

# 2. Three-Agent Parallel Strategy

## Cursor Agent 1 — Foundation & UI

Primary responsibility:

- React/Vite/TypeScript foundation
- Application shell
- Routing
- Header/navigation/sidebar
- Design tokens
- Shared UI components
- Glassmorphism
- Liquid visual system
- Responsive layout primitives
- Theme/background system
- Weather-reactive atmosphere
- Shared animations
- Shared utilities/hooks

Primary ownership:

```text
src/app/
src/components/ui/
src/components/layout/
src/components/shared/
src/styles/
src/theme/
src/lib/
src/hooks/shared/
src/routes/
```

Agent 1 should avoid modifying feature-specific weather and AI modules unless a shared component is required.

---

## Cursor Agent 2 — Weather Experience

Primary responsibility:

- Weather dashboard
- Current weather
- Hourly forecast
- Daily forecast
- Weather metrics
- Charts
- Alerts
- Location/search
- Weather maps
- Weather-specific loading/error/empty states
- Weather mock services

Primary ownership:

```text
src/features/weather/
src/features/forecast/
src/features/alerts/
src/features/maps/
src/features/location/
src/pages/weather/
src/services/mock/weather*
src/services/mock/forecast*
src/services/mock/alerts*
```

Agent 2 should consume Agent 1's shared components rather than recreating them.

---

## Cursor Agent 3 — AI & Advanced Features

Primary responsibility:

- WeatherGPT assistant
- Chat interface
- AI message components
- Suggested prompts
- AI loading/error states
- Voice input UI
- Voice output UI
- Speech service abstraction
- Multilingual UI
- English/Hindi/Gujarati support
- Language selector
- AI-specific animations and interactions
- AI mock services

Primary ownership:

```text
src/features/ai/
src/features/chat/
src/features/voice/
src/features/i18n/
src/services/mock/ai*
src/services/mock/voice*
src/pages/assistant/
```

Agent 3 should consume Agent 1's shared components.

---

# 3. Conflict Prevention Rules

1. Do not let multiple agents edit the same feature files at the same time.
2. Shared UI files have one owner: Agent 1.
3. Weather feature files belong to Agent 2.
4. AI/voice/i18n feature files belong to Agent 3.
5. Feature agents must reuse shared components instead of duplicating them.
6. Keep commits small and focused.
7. Never overwrite another agent's changes.
8. Never force-push shared branches.
9. Never commit `.env`, API keys, tokens, passwords, or secrets.
10. Before starting work, synchronize with the current base branch.
11. Before merging, run the relevant build/type/lint checks.
12. Avoid unrelated refactoring inside another agent's ownership area.
13. If a shared component needs a change, coordinate with Agent 1.
14. Keep mock data outside presentation components.
15. Every completed task must leave the project buildable.

---

# 4. Mock Data / Backend-Ready Architecture

The frontend must not hard-code mock data directly inside visual components.

Use:

```text
UI Component
     ↓
Feature hook/service
     ↓
Service abstraction
     ↓
Mock implementation
     ↓
Later: Real backend implementation
```

Use an environment switch such as:

```text
VITE_USE_MOCK_API=true
```

Later:

```text
VITE_USE_MOCK_API=false
```

The UI should not need to change when the implementation switches from mock data to the real backend.

Mock services should cover at least:

- Current weather
- Hourly forecast
- Daily forecast
- Alerts
- Locations
- Maps/layer state where practical
- AI responses
- Voice/transcription state
- Language data

Mock data should include realistic variation and should support:

- normal success
- loading
- errors
- empty results
- different weather conditions
- different locations

---

# 5. PHASE 1 — FOUNDATION & UI SYSTEM

## Phase 1 Goal

Create a strong frontend foundation that all feature work can safely build on.

---

## 1.1 Project Bootstrap

Tasks:

- Initialize React + TypeScript + Vite.
- Configure TypeScript.
- Configure linting and formatting.
- Configure aliases if useful.
- Establish the source directory structure.
- Create environment configuration.
- Add `.env.example`.
- Add a global CSS reset/base.
- Add an error boundary.
- Confirm development build.
- Confirm production build.

Definition of done:

- App starts successfully.
- Production build succeeds.
- No major TypeScript errors.
- Basic architecture is documented.

---

## 1.2 Application Shell

Build:

- Root application layout
- Header
- Navigation
- Main content area
- Desktop shell
- Mobile shell
- Global background layer
- Page transition foundation

Requirements:

- Responsive
- Keyboard accessible
- Stable layout
- No major layout shifts

---

## 1.3 Routing & Navigation

Create the initial routes, for example:

```text
/
/dashboard
/forecast
/maps
/alerts
/assistant
/settings
```

Include:

- active navigation
- mobile navigation
- back navigation where useful
- not-found page
- route loading states

---

## 1.4 Design System

Define reusable tokens for:

- typography
- spacing
- border radius
- shadows
- glass surfaces
- blur
- opacity
- breakpoints
- motion duration
- z-index layers
- layout widths

Avoid arbitrary values repeated throughout components.

---

## 1.5 Shared UI Components

Create reusable components such as:

- Button
- IconButton
- Input
- Search
- Select
- Dropdown
- Modal
- Drawer
- Tabs
- Card
- GlassCard
- Badge
- Tooltip
- Toast
- Skeleton
- Spinner
- EmptyState
- ErrorState
- Toggle
- Slider
- Divider

Every interactive component should have appropriate:

- default
- hover
- focus
- active
- disabled
- loading
- error

states where applicable.

---

## 1.6 Glassmorphism + Liquid UI

Create the WeatherGPT visual identity:

- translucent surfaces
- layered blur
- subtle borders
- depth
- soft highlights
- liquid/glass texture
- controlled gradients
- atmospheric layers

The result should look premium and modern, not visually noisy.

Maintain readability over visual effects.

---

## 1.7 Weather-Reactive Atmosphere

Create a reusable background system supporting:

```text
Sunny
Cloudy
Rain
Storm
Snow
Fog
Night
```

Support:

- day/night variations
- subtle atmospheric motion
- condition-specific visual treatment
- graceful fallback
- low-power/reduced-motion behavior

---

## 1.8 Motion System

Create reusable animation patterns for:

- page transitions
- card entrance
- hover
- press
- modal/drawer
- loading
- list appearance
- atmospheric motion

Respect:

```text
prefers-reduced-motion
```

Animation should communicate state and hierarchy.

---

# 6. PHASE 2 — WEATHER EXPERIENCE

## Phase 2 Goal

Build the complete core weather product using realistic mock services.

---

## 2.1 Main Weather Dashboard

Build:

- selected location
- current temperature
- feels-like temperature
- condition
- high/low
- humidity
- wind
- pressure
- visibility
- UV index
- sunrise/sunset
- precipitation information

The layout must adapt rather than simply shrink on smaller screens.

---

## 2.2 Current Weather

Create reusable current-weather components:

- temperature
- weather condition
- weather icon/visual
- feels-like
- high/low
- supporting metrics
- weather-reactive background
- loading
- error

---

## 2.3 Hourly Forecast

Include:

- horizontal forecast timeline
- time
- temperature
- condition
- precipitation probability
- wind where useful

Mobile should support touch-friendly horizontal interaction.

---

## 2.4 Daily Forecast

Include:

- multi-day forecast
- high/low
- condition
- precipitation
- expandable detail where useful

Keep the information hierarchy clear.

---

## 2.5 Weather Charts

Create useful visualizations for:

- temperature
- precipitation
- humidity
- wind
- other useful trends

Charts must:

- resize responsively
- remain readable
- handle missing data
- have loading/error states
- provide accessible labels or alternatives

---

## 2.6 Weather Alerts

Build:

- severity
- alert title
- description
- affected area
- timing
- expandable details

Do not communicate severity through color alone.

---

## 2.7 Location & Search

Build:

- current-location UI
- city/location search
- recent locations
- selected location
- loading state
- no-results state
- location error state

Keep location handling privacy-conscious.

---

## 2.8 Weather Maps

Build the frontend map experience:

- map container
- controls
- layer selector
- weather overlays where practical
- legend
- loading state
- error state
- responsive behavior

Keep map-provider logic isolated behind a clear boundary so it can be changed later.

---

## 2.9 Weather State System

Every major weather feature should support:

```text
Loading
Success
Empty
Error
Retry
```

Avoid blank screens.

---

# 7. PHASE 3 — AI & ADVANCED FEATURES

## Phase 3 Goal

Build the differentiating WeatherGPT experience and complete the product polish.

---

## 3.1 WeatherGPT Assistant

Build:

- assistant landing page
- chat interface
- user messages
- assistant messages
- timestamps where useful
- suggested questions
- contextual prompts
- typing state
- loading state
- error/retry state

Example prompts:

```text
Will it rain today?
Should I carry an umbrella?
What's the weather tomorrow morning?
Is it a good day for outdoor exercise?
```

---

## 3.2 AI Response Experience

Support:

- typing indicator
- streaming-like visual state if desired
- retry
- copy response
- clear conversation
- empty state
- error state

The interface should clearly distinguish conversational explanation from weather facts where useful.

---

## 3.3 Multilingual System

Initial languages:

- English
- Hindi
- Gujarati

Requirements:

- language selector
- translated navigation
- translated major UI
- translated weather terminology
- translated common prompts
- fallback language
- centralized strings
- no scattered hard-coded user-facing text

Architecture should make future languages easy to add.

---

## 3.4 Voice Input

Build:

- microphone control
- permission state
- listening state
- transcription state
- cancellation
- error handling
- unsupported-browser state

Speech APIs must be accessed through a service abstraction.

---

## 3.5 Voice Output

Build:

- speak control
- speaking state
- stop/pause where supported
- language-aware output
- unsupported/unavailable state

Keep speech implementation replaceable.

---

## 3.6 Advanced Interactions

Add selectively:

- 3D hover effects
- depth
- subtle parallax
- interactive controls
- liquid transitions
- weather-reactive motion
- premium micro-interactions

Do not sacrifice usability or performance for effects.

---

# 8. Accessibility

The complete frontend must support:

- semantic HTML
- keyboard navigation
- visible focus
- accessible labels
- sufficient contrast
- screen-reader-friendly controls
- reduced motion
- accessible chart alternatives
- non-color-only status indicators
- appropriate ARIA

Accessibility is part of definition of done.

---

# 9. Responsive Design

Test at:

```text
Mobile
Tablet
Laptop
Desktop
Large desktop
```

Pay special attention to:

- navigation
- dashboard cards
- charts
- maps
- chat
- voice controls
- long AI responses
- touch targets
- landscape mobile

---

# 10. Performance

Avoid:

- unnecessary re-renders
- huge assets
- excessive animation
- blocking initialization
- unnecessary dependencies

Use where appropriate:

- lazy loading
- code splitting
- optimized images
- memoization
- deferred non-critical work

Do not over-optimize before functionality is stable.

---

# 11. Definition of Done

A feature is complete only when:

### Functionality

- Main interaction works.
- Happy path works.
- Loading state works.
- Error state works.
- Empty state works where relevant.
- Retry works where relevant.

### UI

- WeatherGPT design language is followed.
- Responsive behavior is correct.
- Spacing and typography are consistent.
- Hover/focus/active states work.

### Accessibility

- Keyboard usable.
- Labels available.
- Focus visible.
- Reduced motion respected.

### Code

- Meaningful TypeScript types.
- Shared components reused.
- No unnecessary duplication.
- Mock data isolated from presentation.
- No secrets committed.

### Quality

- No major console errors.
- Build succeeds.
- Expected viewport sizes tested.

---

# 12. Git Workflow

Current repository structure:

```text
main
├── frontend-development
├── backend-development
└── integration
```

For parallel frontend work, create separate feature branches/worktrees from:

```text
frontend-development
```

Suggested:

```text
frontend-ui-agent
frontend-weather-agent
frontend-ai-agent
```

Workflow:

```text
frontend-development
       ↓
feature branch/worktree
       ↓
Cursor development
       ↓
test
       ↓
commit
       ↓
push
       ↓
review
       ↓
merge into frontend-development
       ↓
final QA
       ↓
main
```

Do not merge unfinished work into `main`.

---

# 13. Commit Convention

Use focused commits such as:

```text
feat(ui): add glass card system
feat(shell): add responsive navigation
feat(weather): add current weather dashboard
feat(forecast): add hourly forecast
feat(alerts): add weather alert cards
feat(maps): add weather map experience
feat(ai): add WeatherGPT chat
feat(voice): add voice interaction
feat(i18n): add Hindi and Gujarati support
fix(weather): handle missing forecast data
refactor(ui): extract shared loading state
```

Avoid vague messages like:

```text
update
changes
final
stuff
```

---

# 14. Agent Handoff Protocol

Before stopping:

1. Complete or clearly document the current task.
2. Run relevant checks.
3. Commit completed work.
4. List changed files.
5. List remaining work.
6. Mention shared files changed.
7. Do not intentionally leave broken imports.

Example:

```text
Completed:
- Current weather card
- Weather metrics
- Loading/error states

Changed:
- src/features/weather/...
- src/services/mock/...

Checks:
- TypeScript: passed
- Build: passed

Remaining:
- Forecast integration
```

---

# 15. Recommended Execution Order

The agents can work in parallel, but the foundation has dependencies.

## Initial foundation

Agent 1:

```text
Project setup
→ architecture
→ design tokens
→ shared UI
→ application shell
```

Agent 2:

```text
Weather feature structure
→ weather models/types
→ mock weather service
→ dashboard
→ forecast
```

Agent 3:

```text
AI feature structure
→ AI types
→ mock AI service
→ chat
→ voice
→ i18n
```

Once shared UI foundations are available:

Agent 1:

```text
Navigation
→ responsive shell
→ animation system
→ background system
```

Agent 2:

```text
Charts
→ alerts
→ location
→ maps
→ weather polish
```

Agent 3:

```text
Multilingual UI
→ voice states
→ AI polish
→ advanced interactions
```

Final stage:

```text
Merge
→ integration testing
→ responsive QA
→ accessibility QA
→ performance QA
→ visual QA
→ bug fixing
→ SIH demo polish
```

---

# 16. Final Frontend Quality Bar

WeatherGPT should feel like a serious product rather than a collection of demo components.

The finished frontend should have:

- coherent visual identity
- excellent information hierarchy
- premium glass/liquid UI
- weather-reactive atmosphere
- polished weather visualization
- responsive layouts
- convincing AI assistant experience
- multilingual support
- voice interaction
- accessible interaction
- robust loading/error handling
- clean maintainable architecture
- backend-ready service abstraction
- smooth but purposeful animations
- strong SIH presentation quality

The final quality question:

> Would this look and behave like a serious SIH finalist product?

If not, continue polishing.

---

# 17. Final Verification Checklist

- [ ] Project builds successfully
- [ ] No major TypeScript errors
- [ ] No major console errors
- [ ] Navigation works
- [ ] Dashboard works
- [ ] Current weather works
- [ ] Hourly forecast works
- [ ] Daily forecast works
- [ ] Charts work
- [ ] Alerts work
- [ ] Location/search works
- [ ] Maps work or have an integration-ready implementation
- [ ] WeatherGPT chat works with mock service
- [ ] Voice UI works or gracefully handles unsupported environments
- [ ] English works
- [ ] Hindi works
- [ ] Gujarati works
- [ ] Loading states exist
- [ ] Error states exist
- [ ] Empty states exist
- [ ] Mobile works
- [ ] Tablet works
- [ ] Desktop works
- [ ] Keyboard navigation works
- [ ] Reduced motion works
- [ ] Performance is acceptable
- [ ] No secrets are committed
- [ ] Mock services are isolated from UI
- [ ] Real backend can later replace mock services
- [ ] Final visual QA completed
- [ ] SIH demo flow tested

---

# 18. Relationship to Existing Project Documents

This roadmap is used together with:

- `FRONTEND_MASTER_PROMPT.txt`
- `PROJECT_CONTEXT.md`

Use them differently:

### FRONTEND_MASTER_PROMPT.txt

Defines what WeatherGPT should look like and what frontend capabilities it should provide.

### PROJECT_CONTEXT.md

Preserves project context, decisions, architecture rules, progress and session handoff information.

### FRONTEND_ROADMAP.md

Defines how the frontend will actually be executed, including the three phases, Cursor-agent ownership, task order, conflict prevention, mock architecture and definition of done.

---

# 19. Immediate Next Steps

1. Create the frontend application inside `frontend/`.
2. Establish the base architecture.
3. Confirm the folder structure.
4. Commit the foundation to `frontend-development`.
5. Create separate frontend feature branches/worktrees for the three Cursor agents.
6. Give each Cursor agent its dedicated task prompt.
7. Develop the three workstreams in parallel.
8. Merge progressively into `frontend-development`.
9. Run full frontend integration and QA.
10. Polish for SIH demonstration.
11. Only after the frontend is stable, connect it to the real backend.

Do not begin all three agents by giving them the entire repository. Give each agent a clearly bounded responsibility.
