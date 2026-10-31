import { AgentClient } from "./client.js";
const client = new AgentClient("http://127.0.0.1:8765", async () => "mock-user");
async function main(): Promise<void> {
  const result = await client.invoke("agent-demo", {
    input: { type: "message", content: "hello" },
    context: { tenantId: "tenant-demo", dataClassification: "internal" },
    execution: { mode: "sync", timeoutMs: 5000 }
  }, "typescript-demo");
  console.log(JSON.stringify(result, null, 2));
}
void main();

