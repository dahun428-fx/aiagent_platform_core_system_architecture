export type Classification = "public" | "internal" | "confidential" | "restricted";
export interface InvocationRequest {
  input: { type: "message"; content: string };
  context: { tenantId: string; dataClassification: Classification };
  execution: { mode: "sync" | "async" | "durable"; timeoutMs: number };
}
export interface InvocationResult {
  invocationId: string;
  agentVersion: string;
  status: "succeeded";
  output: { type: "message"; content: string };
  traceparent: string;
  routeDecisionId: string;
  usage: { inputTokens: number; outputTokens: number };
}
export interface ExecutionStatus {
  invocationId: string;
  revision: number;
  state: "accepted" | "running" | "waiting_approval" | "cancel_requested" | "cancelled" | "succeeded" | "failed" | "rejected" | "expired" | "unknown_outcome";
  policyVersion: string;
}
export interface Problem {
  type: string;
  title: string;
  status: number;
  code: string;
  traceId: string;
  detail?: string;
}
export class GatewayError extends Error {
  constructor(readonly status: number, readonly problem: unknown) {
    super("Agent Gateway request failed: " + status);
  }
}
function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function result(value: unknown): value is InvocationResult {
  if (!object(value) || !object(value.output) || !object(value.usage)) return false;
  return typeof value.invocationId === "string" && typeof value.agentVersion === "string" &&
    value.status === "succeeded" && value.output.type === "message" &&
    typeof value.output.content === "string" && typeof value.traceparent === "string" &&
    typeof value.routeDecisionId === "string" && Number.isInteger(value.usage.inputTokens) &&
    Number.isInteger(value.usage.outputTokens);
}
function execution(value: unknown): value is ExecutionStatus {
  return object(value) && typeof value.invocationId === "string" &&
    Number.isInteger(value.revision) && typeof value.state === "string" &&
    ["accepted", "running", "waiting_approval", "cancel_requested", "cancelled", "succeeded", "failed", "rejected", "expired", "unknown_outcome"].includes(value.state) &&
    typeof value.policyVersion === "string";
}
export class AgentClient {
  constructor(private readonly baseUrl: string, private readonly getToken: () => Promise<string>) {
    const u = new URL(baseUrl);
    if (u.protocol !== "https:" && !(u.protocol === "http:" && ["127.0.0.1", "localhost"].includes(u.hostname))) {
      throw new Error("HTTPS required outside loopback");
    }
  }
  async invoke(agentId: string, request: InvocationRequest, key: string, traceparent?: string): Promise<InvocationResult | ExecutionStatus> {
    if (!key.trim()) throw new Error("Idempotency key required");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + await this.getToken(),
      "Idempotency-Key": key
    };
    if (traceparent) headers.traceparent = traceparent;
    // No automatic retry for writes or unknown effects. A caller may explicitly replay the same request/key.
    const response = await fetch(this.baseUrl.replace(/\/$/, "") + "/v1/agents/" + encodeURIComponent(agentId) + "/invocations", {
      method: "POST", headers, body: JSON.stringify(request), signal: AbortSignal.timeout(request.execution.timeoutMs)
    });
    const body: unknown = await response.json();
    if (!response.ok) throw new GatewayError(response.status, body);
    if (response.status === 200 && result(body)) return body;
    if (response.status === 202 && execution(body)) return body;
    throw new Error("Gateway response does not match supported response contract");
  }
}

