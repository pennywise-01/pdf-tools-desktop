# Part 1: Frontend Guidelines

## Design Thinking

Before coding, define:
- **Purpose**: What problem does this solve? Who uses it?
- **Tone**: Choose a bold direction (minimal, maximalist, retro-futuristic, brutalist, luxury, playful, etc.)
- **Constraints**: Framework, performance, accessibility requirements
- **Differentiation**: What makes this memorable?

**Key Principle**: Intentionality over intensity. Execute your chosen direction with precision.

## Core Elements

### Typography
- Use distinctive, characterful fonts—avoid generic (Arial, Inter, Roboto, system fonts)
- Pair a display font with a refined body font

### Color & Theme
- Use CSS variables for consistency
- Bold dominant colors with sharp accents > evenly-distributed palettes
- Avoid clichés (e.g., purple gradients on white)

### Motion & Animation
- Prioritize CSS-only solutions; use Motion library for React
- Focus on high-impact moments (staggered page loads, scroll-triggers, surprising hover states)

### Layout
- Embrace asymmetry, overlap, diagonal flow, grid-breaking elements
- Use generous negative space OR controlled density intentionally

### Visual Details
- Create depth with gradients, textures, patterns, shadows, overlays
- Never default to flat solid colors

## Rules
- Every design should be unique—vary themes, fonts, aesthetics
- Match code complexity to the vision (elaborate for maximalist, restrained for minimal)
- Make unexpected, context-specific choices

---

# Part 2: Backend Guidelines

## Core Principles

### Code Quality
- Write clean, readable, self-documenting code
- Follow language-specific style guides (PEP 8 for Python, etc.)
- Use meaningful variable/function names
- Keep functions small and single-purpose (Single Responsibility Principle)

### Architecture
- Follow SOLID principles
- Use appropriate design patterns (Repository, Factory, Strategy, etc.)
- Separate concerns: controllers, services, repositories, models
- Keep business logic out of controllers/routes

### Error Handling
- Use try-except blocks appropriately
- Create custom exception classes for domain-specific errors
- Log errors with context (timestamp, request ID, stack trace)
- Return meaningful error messages to clients

### Security
- Validate and sanitize all inputs
- Use parameterized queries (prevent SQL injection)
- Implement proper authentication/authorization
- Never expose sensitive data in logs or responses
- Follow OWASP security guidelines

### Performance
- Use caching strategically (Redis, in-memory)
- Optimize database queries (indexing, pagination, lazy loading)
- Implement connection pooling
- Use async/await for I/O-bound operations

### Testing
- Write unit tests for business logic
- Write integration tests for APIs
- Aim for meaningful coverage, not 100%
- Use mocking for external dependencies

### Documentation
- Document public APIs (docstrings, OpenAPI/Swagger)
- Include setup instructions in README
- Document environment variables and configuration

### Logging & Monitoring
- Use structured logging (JSON format)
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include correlation IDs for request tracing

### Database
- Use migrations for schema changes
- Follow naming conventions (snake_case for tables/columns)
- Design for normalization, denormalize when needed for performance
- Always use transactions for multi-step operations

### API Design
- Follow REST conventions (proper HTTP methods and status codes)
- Use consistent naming (plural nouns for resources)
- Version your APIs
- Implement rate limiting