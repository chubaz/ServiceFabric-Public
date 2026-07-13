# Getting Started with ServiceFabric Workspaces

Welcome to the new ServiceFabric Workspace architecture!

ServiceFabric now uses an **external multi-application development workspace**. This means your application source code lives outside of the core ServiceFabric repository, keeping your code safe, portable, and cleanly separated from the platform's internal state.

## Concepts

Your new environment is split into two distinct areas:

1. **The Workspace (`SERVICEFABRIC_WORKSPACE`)**: The visible folder where you (and coding assistants like Claude or Gemini) do your work. It contains your application source code, shared libraries, and recipes.
2. **The Platform State (`SERVICEFABRIC_HOME`)**: A hidden folder (`.servicefabric` by default) managed entirely by the ServiceFabric CLI. It contains builds, running processes, logs, artifacts, and databases. You shouldn't need to touch this folder manually.

## Creating Your First Workspace

Choose a location on your computer for your workspace (e.g., `~/Projects/ServiceFabricWorkspace`) and initialize it:

```bash
# 1. Initialize the workspace
servicefabric workspace init ~/Projects/ServiceFabricWorkspace

# 2. Enter your workspace
cd ~/Projects/ServiceFabricWorkspace
```

*(Note: If you run ServiceFabric commands from inside this directory, the CLI automatically detects it as your workspace.)*

## Anatomy of the Workspace

Once initialized, your workspace will look like this:

```text
ServiceFabricWorkspace/
├── workspace.yaml       # Workspace configuration
├── applications/        # Where your application projects live
├── recipes/             # Reusable application templates
├── libraries/           # Shared code libraries
└── .servicefabric/      # (Hidden) Platform-managed state (do not edit!)
```

## Creating an Application

To create a new, empty application project, use the CLI:

```bash
servicefabric apps create my-first-app --empty
```

This generates a structured, assistant-ready application folder in `applications/my-first-app/`:

```text
applications/my-first-app/
├── README.md            # What your app does
├── AGENTS.md            # Instructions for coding assistants
├── ARCHITECTURE.md      # How your app is designed
├── DEVELOPMENT.md       # Commands to build, run, and test
├── modules/             # Your application code (frontend, api, worker)
├── tests/               # Your tests
└── .servicefabric/
    └── application.yaml # The declarative identity of your app
```

## Working with Coding Assistants

The new workspace model is designed specifically for AI coding assistants. When asking an assistant to build a feature:

1. Point the assistant directly at your specific application directory (`applications/my-first-app/`).
2. The `AGENTS.md` file explicitly tells the assistant what it can and cannot do (e.g., "Do not modify `.servicefabric` files", "Only edit files in `modules/`").
3. The assistant will safely edit your source code without accidentally modifying the ServiceFabric platform code or runtime state.

## Lifecycle Commands

As you develop, you'll use the CLI to manage your app's lifecycle:

- `servicefabric apps build my-first-app`: Compiles your source into a locked, immutable artifact.
- `servicefabric apps start my-first-app`: Launches your application into an isolated local process.
- `servicefabric apps status my-first-app`: Checks if your application is running and healthy.
- `servicefabric apps resources my-first-app`: Views the memory and CPU usage of your running app.
- `servicefabric apps stop my-first-app`: Safely stops the running process.

## Frequently Asked Questions

**Q: Where did my database data go?**
A: It is managed safely by ServiceFabric inside the hidden `.servicefabric/resources/` directory.

**Q: Can I use git?**
A: Yes! You should initialize a git repository in your Workspace directory (or inside individual application directories). Ensure you ignore the `.servicefabric/` folder so you don't commit temporary builds and logs!

**Q: What about the old `6_service_catalog`?**
A: Legacy applications in the ServiceFabric repository will continue to work for now, but new applications should be created in your external workspace.