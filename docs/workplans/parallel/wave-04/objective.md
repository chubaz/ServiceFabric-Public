# Wave-4 Objective

Introduce explicit application-native operations and capabilities, register validated capability definitions in the local ServiceFabric workspace, and prove the model with Research Notes.

The acceptance journey is:

```text
servicefabric workspace init WORKSPACE
servicefabric apps create research-notes --template modular-web-app
servicefabric capabilities validate research-notes
servicefabric capabilities register research-notes
servicefabric capabilities list
servicefabric capabilities describe notes.create
```

Wave 4 does not invoke capabilities, publish MCP tools, create REST or Python projections, infer capabilities from routes, change AP-01A behavior, replace ToolDefinition, or implement runtime availability. The registry stores static definitions only; projections belong to Wave 6 and runtime availability to Wave 5.
