Project: Moodle Wrapper

Type: Integration Service / API Gateway
Domain: Education / LMS automation

Description:
This project is a wrapper around Moodle that exposes a cleaner,
more predictable API and enables automation, integrations, and
business logic on top of Moodle without modifying Moodle core.

It must:

- Never alter Moodle core code
- Communicate only through Moodle APIs or official endpoints
- Be fully replaceable if Moodle is swapped later

Style:

- API-first
- Stateless services
- Clear separation between:
  - Moodle communication layer
  - Business logic layer
  - Public API layer

Architecture Principles:

1. Moodle is infrastructure, not the domain
   Moodle is treated like:

- a database
- or an external service
  Never like the source of truth for business rules.

2. Wrapper defines the domain
   All business concepts live in the wrapper:

- Users
- Courses
- Enrollments
- Progress
- Permissions

3. Idempotent operations
   Calling the same action twice must not break state.

4. Strong error normalization
   Moodle errors must be translated into:

- Clean error codes
- Predictable JSON responses
- No Moodle-specific noise leaking outward

5. Observability first
   Every Moodle call must be:

- Logged
- Measurable
- Traceable

6. Security:

- JWT required for all external endpoints
- Moodle credentials never exposed
- Token rotation supported

Priorities:

- Stability over speed
- Explicit behavior over magic
- Clear domain boundaries
- Easy debugging

Non-goals:

- Rebuilding Moodle features
- Tight coupling to Moodle internal schema
- UI concerns (this is backend-only)
