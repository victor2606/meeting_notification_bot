<related_docs>
  <doc href="docs/architecture.md">Project architecture, data flow, component structure</doc>
  <doc href="docs/CODE_STYLE.md">Code style guidelines, naming conventions, formatting rules</doc>
</related_docs>

<project_instructions>

<critical_rules description="Never Violate">
  <rule id="1" name="Fail Fast">Invalid input or state → raise error immediately. Never continue with partial/default data.</rule>
  <rule id="2" name="No Silent Failures">Catch only expected exceptions → log with context → re-raise. No empty catch blocks.</rule>
  <rule id="3" name="No Invented Defaults">Never mask missing required data with fallback values. Missing config = error.</rule>
  <rule id="4" name="No Hidden Retries">Retry only if: explicitly requested + idempotent + transient error + bounded attempts + logged.</rule>
  <rule id="5" name="Observability">Structured logging on every failure. Never downgrade error to warning.</rule>
  <rule id="6" name="Security First">Verify authorization on every new endpoint/page. No credentials in code.</rule>
</critical_rules>

<execution_model>
  <parallel_first_principle>
    <default>parallel. Sequential only when proven dependency exists.</default>
    <usage tool="claude-code-mcp">Launch multiple subagents in ONE message</usage>
    <guidelines>
      <item>Independent file edits → parallel</item>
      <item>Independent analysis tasks → parallel</item>
      <item>All QA tasks → ALWAYS parallel (review, tests, security, performance)</item>
    </guidelines>
    <sequential_condition>Only when output of Task A is input for Task B</sequential_condition>
  </parallel_first_principle>

  <limits>
    <limit name="parallel_subagents">Max 10 per batch</limit>
    <limit name="queue_size">Up to 100 tasks</limit>
    <limit name="context">Each subagent has isolated context (no shared state)</limit>
    <limit name="nesting">Subagents cannot spawn subagents</limit>
  </limits>

  <batched_execution_pattern>
    <batch order="1" mode="parallel">Analysis/exploration subagents → Wait for results</batch>
    <batch order="2" mode="parallel">Implementation subagents → Wait for results</batch>
    <batch order="3" mode="parallel">QA + documentation subagents</batch>
  </batched_execution_pattern>
</execution_model>

<code_standards>
  <architecture>
    <layers>Handlers → Services → Models (or equivalent for your stack)</layers>
    <file_size max="500">Split by responsibility if exceeded</file_size>
    <nesting max="3">Flatten complex conditions</nesting>
    <dependencies>Explicit only. No global state, no hidden coupling.</dependencies>
  </architecture>

  <anti_patterns description="Avoid">
    <pattern>Implicit dependencies between modules</pattern>
    <pattern>Deep inheritance hierarchies</pattern>
    <pattern>Complex patterns (Observer, Strategy, Factory-of-Factories) unless already in codebase</pattern>
    <pattern>Multiple ways to do the same thing</pattern>
  </anti_patterns>

  <testing>
    <rule>Write tests for new code</rule>
    <rule>E2E: headless mode + screenshots on completion</rule>
    <rule>Mocks: separate folder, cover success/error/timeout scenarios</rule>
    <rule>Delete temporary test files after checks complete</rule>
  </testing>
</code_standards>

<file_and_documentation>
  <structure>
    <rule>Related functionality → one folder</rule>
    <rule>Tests next to code they test</rule>
    <rule>Documentation in `docs/` folder only</rule>
  </structure>

  <when_to_update_docs>
    <trigger>API changes → update immediately</trigger>
    <trigger>Architecture changes → update immediately</trigger>
    <trigger>Completing a task → check if docs need update (MANDATORY check)</trigger>
  </when_to_update_docs>

  <file_documentation>
    <rule>Brief description at file start with key methods/functions and line numbers</rule>
    <rule>Update when modifying file</rule>
  </file_documentation>

  <when_not_to_create_docs>
    <rule>After task completion (unless explicitly requested)</rule>
    <rule>README files not requested by user</rule>
  </when_not_to_create_docs>
</file_and_documentation>

<tools_usage>
  <shell_commands>
    <rule>Use `python3` (not `python`) — macOS default</rule>
    <rule>Run linters: `python3 -m ruff` (not `uv run ruff` — ruff not in uv deps)</rule>
    <rule>Run tests: `uv run pytest`</rule>
  </shell_commands>

  <code_search priority="highest">
    <instruction>ALWAYS use `mcp__claude-context__search_code` FIRST for any codebase exploration.</instruction>
    <workflow>
      <step order="1">Search with `search_code` (hybrid: semantic + keyword)</step>
      <step order="2">Use results to identify relevant files</step>
      <step order="3">Then read specific files if needed</step>
    </workflow>
    <rationale>Semantic search finds related code even without exact keywords. Grep/find miss conceptual matches.</rationale>
    <parameters>
      <param name="query">natural language OR exact identifiers (both work)</param>
      <param name="extensionFilter">narrow by file type when needed</param>
      <param name="limit" default="10" max="50"/>
    </parameters>
    <warning>NEVER use `clear_index` — rebuild takes hours</warning>
  </code_search>

  <library_docs tool="context7">
    <rule>Use for up-to-date documentation of libraries</rule>
    <rule>Always check before using unfamiliar APIs</rule>
  </library_docs>

  <browser_testing tool="chrome-devtools">
    <rule>Use for E2E verification</rule>
    <rule>Take screenshots on test completion</rule>
    <rule>Analyze screenshots even on success</rule>
  </browser_testing>

  <sequential_thinking>
    <use_case>Complex multi-step reasoning</use_case>
    <use_case>When standard approach leads to errors</use_case>
  </sequential_thinking>
</tools_usage>

<workflow_phases>
  <phase order="1" name="Analysis">
    <step priority="first">Use `search_code` to explore codebase (not grep/find)</step>
    <step>Study current implementation</step>
    <step>Ask clarifying questions about constraints and edge cases</step>
    <step>Check impact on other components</step>
    <parallelization>Independent module analysis</parallelization>
  </phase>

  <phase order="2" name="Implementation">
    <step>Write/edit code</step>
    <step>Run linter on modified files</step>
    <step>Fix errors immediately before proceeding</step>
    <parallelization>Independent file modifications</parallelization>
  </phase>

  <phase order="3" name="Quality Assurance">
    <instruction>ALWAYS PARALLEL: Launch all QA subagents simultaneously</instruction>
    <tasks>
      <task>Code review</task>
      <task>Tests</task>
      <task>Security audit</task>
      <task>Performance check</task>
    </tasks>
    <rule>Never wait for one QA task before starting another</rule>
  </phase>

  <phase order="4" name="Finalization">
    <step>Update documentation if API/architecture changed</step>
    <step>Final linter check</step>
    <step>Remove temporary files</step>
  </phase>
</workflow_phases>

<quick_reference>
  <decision_table name="Parallel or Sequential">
    <row condition="Tasks independent?" action="PARALLEL"/>
    <row condition="Task B needs Task A output?" action="SEQUENTIAL"/>
    <row condition="QA tasks?" action="ALWAYS PARALLEL"/>
    <row condition="Exploring codebase?" action="PARALLEL per module"/>
    <row condition="Editing multiple files?" action="PARALLEL if independent"/>
  </decision_table>

  <decision_table name="On Error">
    <row condition="Missing required data?" action="Raise, don't default"/>
    <row condition="Unexpected exception?" action="Log context, re-raise"/>
    <row condition="External API failed?" action="Log, raise (no retry)"/>
    <row condition="Linter error?" action="Fix immediately"/>
  </decision_table>

  <checklist name="After Each Task">
    <item>Linter passed?</item>
    <item>Tests written/updated?</item>
    <item>Docs need update? (API/architecture changed?)</item>
    <item>Temporary files deleted?</item>
  </checklist>
</quick_reference>

</project_instructions>