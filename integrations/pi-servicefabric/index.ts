export type ServiceFabricInvoker = (toolId: string, args: unknown) => Promise<unknown>;

export function createServiceFabricExtension(invoke: ServiceFabricInvoker) {
  return {
    name: "servicefabric",
    tools: ["math.calculate", "research.search_papers", "research.prepare_literature_review"].map((toolId) => ({
      name: toolId.replaceAll(".", "_"),
      invoke: (args: unknown) => invoke(toolId, args),
    })),
  };
}
