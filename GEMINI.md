# Agent Instructions

The rules specified here are to guide implementation based on various principles and guidelines. This helps to achieve consistency and reliability as LLMs tend to be probabilistic. Also, refer to industry standards and best practices when making any changes.


## Operating Principles

**1. Simplicity first**
- Before writing new code, check if the existing functionality already exists. If it does, use it or possibly refactor it.
- When interacting with libraries, frameworks, or APIs, find or ask user for link to documentations and understand them before implementing.
- Strive for simple and straightforward solutions. Avoid over-engineering or premature optimization.

**2. Incremental changes**
- For big changes, don't try to implement everything in one go.
- Make small incremental changes and test after each change.
- This helps to catch errors early and makes it easier to debug.

**3. Self-anneal when things break**
- Read error message and stack trace.
- Fix the code and test it again (unless it uses paid tokens/credits/etc, in which case you check w user first).
- Update the documentation with what you learned (API limits, timing, edge cases). Whenever you encounter an error, refer to this document and check if a similar issue has occurred before. If yes, try the attempted solution.
- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite code to accommodate → test → update documentation.

**4. Update documentation as you learn**
- Documentation are living documents. When you discover architectural issues, API constraints, better approaches, common errors, or timing expectations, you should update the documentation. But don't create or overwrite documentation without asking unless explicitly told to. Documentation are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

**5. Update the README.md and ensure that it is up to date and consistent with the codebase**
- Maintain a README.md with a high level architecture diagram of the system. This should be a technical document that explains the system in detail. 
- Clearly explain design choices and trade-offs in the documentation. 
- Give a quick overview of the project structure and what goes where.
- Quick start guide for setting up the project locally and how to test or run it.
- Ensure that the README.md is updated whenever you make changes to the codebase.