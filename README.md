# WeatherGPT

AI-powered conversational weather intelligence platform for the Smart India Hackathon (SIH).

## Project Status

🚧 Under Development

## Tech Stack

- Frontend: React
- Backend: FastAPI
- AI: LLM
- Database: PostgreSQL

## Backend

The backend provides conversational weather intelligence through:

- Real-time weather information
- Forecasts and historical weather
- Natural-language weather queries
- GFS / NWP integration
- Official IMD warnings
- Weather-based recommendations
- Disaster and extreme-weather risk detection
- Conversation context
- PostgreSQL persistence
- Caching and performance optimization

## Project Structure

```text
WeatherGPT/
├── api-contract/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   └── services/
│   └── tests
├── docs/
├── frontend/
├── integration/
├── PROJECT_CONTEXT.md
├── FRONTEND_ROADMAP.md
├── README.md
└── .gitignore