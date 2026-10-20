---
description: "Use for this SQL Crash Course project when changing the FastAPI backend, SQLModel models, SQLite database, or Next.js frontend."
applyTo:
  <!-- - "BACKEND/main.py"
  - "BACKEND/config/**/*.py"
  - "BACKEND/controllers/**/*.py"
  - "BACKEND/models/**/*.py"
  - "BACKEND/routes/**/*.py"
  - "DATABASE/**/*.sql"
  - "FRONTEND/sql-practice/src/**/*.js"
  - "FRONTEND/sql-practice/src/**/*.jsx"
  - "FRONTEND/sql-practice/src/**/*.css"
--- -->

# SQLCrashCourse — Coding Rules

## 1. Simplicity and readability

1. Write code simple enough for beginners to understand.
2. Keep code production-quality without unnecessary complexity.
3. Prioritize readability over clever shortcuts.
4. Give every file one clear responsibility.
5. Create the fewest files possible.
6. Reuse existing code before creating new functions or files.
7. Preserve the current project architecture.
8. Make the smallest necessary changes.
9. Use fully descriptive names for variables, functions, classes, parameters, and files.
10. Never sacrifice clarity for shorter code.

## 2. Documentation and comments

1. Important Python and JavaScript files must include a WHAT / WHY / HOW / IMPORTANT header.
2. Explain what each file does and why it exists.
3. Explain how important functions work.
4. Document important dependencies and limitations.
5. Add short, useful comments for learning.
6. Keep code readable from top to bottom, like a story.
7. Avoid unnecessary explanations and excessive comments.
8. Prefer beginner-friendly explanations with practical examples.

## 3. Project architecture

1. **BACKEND/** contains Python backend code.
2. **FRONTEND/** contains React UI and plain JavaScript.
3. **DATABASE/** contains the SQLite database and SQL scripts.
4. **BACKEND/config/DBsetup.py** manages database configuration and connections.
5. **BACKEND/models/** contains SQLModel database models.
6. **BACKEND/controllers/** contains business logic and database operations.
7. **BACKEND/routes/** contains FastAPI endpoints.
8. **BACKEND/main.py** initializes the FastAPI application.
9. React handles UI; use plain JavaScript for other frontend logic unless a library is necessary.
10. The frontend communicates with SQLite through the Python backend, never directly.

## 4. Database and ORM rules

1. Use SQLite as the project's database.
2. Store the database in **DATABASE/practice.db**.
3. Use SQLModel as the ORM, similar to Mongoose.
4. Use SQLAlchemy functionality only when SQLModel requires it.
5. Use `_id` as the database primary-key column for user identification.
6. Generate unique UUID identifiers using Python's built-in `uuid` module.
7. Use SQLModel models as the source of truth for table definitions.
8. Use SQLModel sessions for database operations.
9. Always use parameterized queries or ORM expressions, never string-concatenated SQL with user input.
10. Avoid Alembic until database migrations are actually needed.
11. Use a VS Code SQLite viewer to inspect tables and records.

## 5. Dependencies and tools

1. Use `uv` for Python dependency management.
2. Use Python's built-in functionality whenever possible.
3. Add packages only when they solve a real requirement.
4. Do not introduce Docker, additional database servers, or unnecessary services.
5. Do not install duplicate libraries that perform the same job.
6. Keep project configuration minimal and understandable.

## 6. Validation, security, and reliability

1. Validate external input before database operations.
2. Handle errors explicitly and provide meaningful messages.
3. Never silently ignore important failures.
4. Keep database connections and sessions properly managed.
5. Prevent unnecessary application crashes.
6. Never expose passwords, secrets, or sensitive data.
7. Keep database access and business logic on the backend.
8. Apply database constraints for data integrity.
9. Prioritize correctness before optimization.

## 7. Testing and development

1. Build and test one feature at a time.
2. Verify CRUD operations: Create, Read, Update, Delete.
3. Test normal operations and important failure cases.
4. Preserve working functionality when making changes.
5. Avoid placeholders and unnecessary TODOs.
6. Explain why new files, dependencies, or architectural changes are needed.
7. Use FastAPI `/docs` to test endpoints.
8. Use the SQLite viewer to verify database records.
9. Keep examples small, runnable, and directly relevant to the project.

## Our five highest-priority rules

1. **Simplicity:** Code must be understandable by a beginner.
2. **Descriptive naming:** Names should explain their purpose.
3. **Minimum complexity:** Fewest files, packages, and dependencies.
4. **Correctness:** Data integrity, validation, and reliability come first.
5. **Learning:** Explain what the code does, why it exists, and how it works using concise comments.

## Development philosophy

**Learn → Build → Test → Understand → Improve**

We are building this project to understand SQL, SQLite, SQLModel, FastAPI, and React—not to introduce unnecessary infrastructure or abstractions.

Every new feature must serve a clear learning or application purpose.
