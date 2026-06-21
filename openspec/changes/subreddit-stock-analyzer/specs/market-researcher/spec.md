## ADDED Requirements

### Requirement: Fetch Financial Data and News
For each of the top 5 tickers, the system SHALL query external APIs for current market metrics and recent news.

#### Scenario: API Data Retrieval
- **WHEN** provided with a ticker
- **THEN** the system successfully fetches the financial metrics and top 5 recent news headlines.

### Requirement: Generate Research & Reddit Summary
The system SHALL utilize an LLM (via Pydantic AI) to generate a structured report that includes a summary of the specific Reddit comments, the news, and industry outlook.

#### Scenario: Report Synthesis
- **WHEN** all data (including bundled Reddit text) is collected
- **THEN** the system generates a structured JSON report including a Reddit sentiment summary.

### Requirement: Strict 'Default to HOLD' Signal
The generated research report SHALL include a Buy, Sell, or Hold recommendation. The prompt MUST instruct the LLM to default to "HOLD" unless overwhelming, corroborating positive or negative signals exist.

#### Scenario: Conservative Signal Generation
- **WHEN** the report is generated with mixed or mild signals
- **THEN** the model outputs a "HOLD" recommendation.

### Requirement: LLM Evaluations
The system SHALL include an evaluation suite to programmatically test the accuracy, consistency, and adherence to the "Default to HOLD" rule of the LLM prompts.

#### Scenario: Running Evals
- **WHEN** the developer runs the test suite
- **THEN** the evaluation framework runs predefined test cases against the LLM to verify it doesn't hallucinate or issue unwarranted BUY/SELL signals.
