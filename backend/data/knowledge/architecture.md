# How Maestro works

A request flows through three layers:

1. **Orchestrator** — a routing step that uses the language model to choose
   which specialist agent should handle the request. It picks exactly one agent.
2. **Specialist agent** — runs a reason-and-act loop: it looks at the request,
   decides whether it needs a tool, calls the tool, reads the result, and
   repeats until it can answer.
3. **Tools** — plain Python functions (calculator, unit converter, weather
   lookup, knowledge-base search) that do the real work.

The whole run is streamed to the UI as events, so you can watch the
orchestrator pick an agent and the agent call its tools in real time.

## Why route instead of one big prompt?

Splitting work across focused agents keeps each prompt small and specific,
makes behaviour easier to debug, and lets you add a new capability by writing
one new agent and registering it — without touching the others.
