import type { ApiKey, EventRecord, Incident, IncidentDiagnosis, Project } from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const DEMO = (import.meta.env.VITE_DEMO_MODE ?? "true") === "true";
const key = "rp_access_token";

function token() { return localStorage.getItem(key); }
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  const response = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

const demoProjects: Project[] = [
  { id: "demo-api", name: "Payments API", description: "Core transaction service", github: "github.com/acme/payments", created_at: new Date().toISOString() },
  { id: "demo-web", name: "Customer dashboard", description: "Frontend web application", github: "github.com/acme/dashboard", created_at: new Date().toISOString() },
];
const demoIncidents: Incident[] = [
  { id: "inc-1", project_id: "demo-api", title: "Elevated 5xx rate on /v1/checkout", description: "Server errors crossed the configured threshold.", severity: "critical", status: "open", first_seen_at: new Date(Date.now()-1000*60*42).toISOString(), last_seen_at: new Date(Date.now()-1000*60*2).toISOString(), details: { route: "/v1/checkout", status_code: 500 } },
  { id: "inc-2", project_id: "demo-api", title: "Checkout latency regression", description: "P95 latency increased above baseline.", severity: "high", status: "acknowledged", first_seen_at: new Date(Date.now()-1000*60*130).toISOString(), last_seen_at: new Date(Date.now()-1000*60*20).toISOString(), details: { route: "/v1/checkout", p95_latency: 1820 } },
  { id: "inc-3", project_id: "demo-web", title: "Authentication timeout", description: "Requests to the identity provider timed out.", severity: "medium", status: "resolved", first_seen_at: new Date(Date.now()-1000*60*60*9).toISOString(), last_seen_at: new Date(Date.now()-1000*60*60*7).toISOString(), details: { route: "/auth/callback" } },
];
const demoEvents = (projectId: string): EventRecord[] => Array.from({length: 18}, (_, i) => {
  const bad = i === 1 || i === 8 || i === 14;
  return { id: `evt-${projectId}-${i}`, project_id: projectId, incident_id: bad ? "inc-1" : null, event_type: bad ? "http.error" : "http.request", service_name: projectId === "demo-api" ? "payments-api" : "dashboard-web", trace_id: `tr_${Math.random().toString(36).slice(2,9)}`, timestamp: new Date(Date.now()-i*1000*60*7).toISOString(), created_at: new Date(Date.now()-i*1000*60*7).toISOString(), method: i%3===0?"POST":"GET", route: bad?"/v1/checkout": ["/health","/v1/users","/v1/orders"][i%3], status_code: bad?500: i%5===0?404:200, duration_ms: bad?1200+Math.round(Math.random()*1800):80+Math.round(Math.random()*300), exception_type: bad?"DatabaseTimeout":null, exception_message: bad?"Connection pool exhausted":null, environment: "production", payload: { status_code: bad?500:200, duration_ms: 180+i*23 } };
});
let demoKeys: ApiKey[] = [
  { id: "key-1", key_prefix: "rp_live_a8", is_active: true, created_at: new Date().toISOString(), last_used: new Date(Date.now()-60000*5).toISOString(), project_id: "demo-api" },
  { id: "key-2", key_prefix: "rp_live_k2", is_active: false, created_at: new Date(Date.now()-86400000*3).toISOString(), project_id: "demo-web" },
];

export const api = {
  isDemo: DEMO,
  login: async (email: string, password: string) => {
    if (DEMO) { localStorage.setItem(key, "demo-token"); localStorage.setItem("rp_user", JSON.stringify({ email, username: email.split("@")[0] })); return; }
    const data = await request<{access_token:string;refresh_token:string}>("/auth/login", { method:"POST", body: JSON.stringify({ email, username: email, password }) });
    localStorage.setItem(key, data.access_token); localStorage.setItem("rp_refresh_token", data.refresh_token); localStorage.setItem("rp_user", JSON.stringify({ email, username: email.split("@")[0] }));
  },
  signup: async (username: string, email: string, password: string) => {
    if (DEMO) { localStorage.setItem("rp_user", JSON.stringify({ username, email })); return; }
    await request("/auth/signup", { method:"POST", body: JSON.stringify({ username, email, password }) });
  },
  logout: () => { localStorage.removeItem(key); localStorage.removeItem("rp_refresh_token"); localStorage.removeItem("rp_user"); },
  projects: async (): Promise<Project[]> => DEMO ? demoProjects : request<Project[]>("/projects"),
  createProject: async (data: {name:string;description:string;github:string}) => {
    if (DEMO) { const project = { ...data, id: `demo-${Date.now()}`, created_at: new Date().toISOString() }; demoProjects.push(project); return project; }
    return request<Project>("/projects", { method:"POST", body: JSON.stringify(data) });
  },
  deleteProject: async (id: string) => {
    if (DEMO) { const idx=demoProjects.findIndex(p=>p.id===id); if(idx>=0) demoProjects.splice(idx,1); return; }
    await request(`/projects/${id}`, { method:"DELETE" });
  },
  keys: async (): Promise<ApiKey[]> => DEMO ? demoKeys : request<ApiKey[]>("/api-keys"),
  createKey: async (project_id: string) => {
    if (DEMO) { const raw=`rp_${crypto.randomUUID().replaceAll("-","")}${crypto.randomUUID().replaceAll("-","")}`; const item={id:`key-${Date.now()}`,key_prefix:raw.slice(0,10),is_active:true,created_at:new Date().toISOString(),project_id}; demoKeys=[{...item},...demoKeys]; return {key:raw,api_key:item}; }
    return request<{key:string;api_key:ApiKey}>("/api-keys", { method:"POST", body: JSON.stringify({ project_id }) });
  },
  revokeKey: async (id: string) => {
    if (DEMO) { demoKeys=demoKeys.map(k=>k.id===id?{...k,is_active:false}:k); return; }
    await request(`/api-keys/${id}`, { method:"DELETE" });
  },
  events: async (projectId: string): Promise<EventRecord[]> => DEMO ? demoEvents(projectId) : (await request<{items:EventRecord[]}>(`/projects/${projectId}/events?limit=100`)).items,
  incidents: async (projectId: string, status?: string): Promise<Incident[]> => {
    if (DEMO) return demoIncidents.filter(i=>i.project_id===projectId && (!status || status==="all" || i.status===status));
    const query = status && status!=="all" ? `?status=${encodeURIComponent(status)}&limit=100` : "?limit=100";
    return request<Incident[]>(`/projects/${projectId}/incidents${query}`);
  },
  updateIncident: async (projectId: string, incidentId: string, status: Incident["status"]) => {
    if (DEMO) { const incident=demoIncidents.find(i=>i.id===incidentId); if(incident) incident.status=status; return incident; }
    return request<Incident>(`/projects/${projectId}/incidents/${incidentId}/status`, { method:"PATCH", body:JSON.stringify({status}) });
  },
  evidence: async (projectId: string, incidentId: string): Promise<EventRecord[]> => DEMO ? demoEvents(projectId).filter(e=>e.incident_id===incidentId) : request<EventRecord[]>(`/projects/${projectId}/incidents/${incidentId}/evidence`),
  diagnosis: async (projectId: string, incidentId: string): Promise<IncidentDiagnosis> => {
    if (DEMO) return { id: `diagnosis-${incidentId}`, incident_id: incidentId, summary: "The failing dependency exhausted its connection pool.", possible_causes: [], recommendations: [], howsolved: "", model_name: "demo", created_at: new Date().toISOString() };
    return request<IncidentDiagnosis>(`/projects/${projectId}/incidents/${incidentId}/diagnosis`);
  },
  updateDiagnosis: async (projectId: string, incidentId: string, howsolved: string): Promise<IncidentDiagnosis> => {
    if (DEMO) return { id: `diagnosis-${incidentId}`, incident_id: incidentId, summary: "", possible_causes: [], recommendations: [], howsolved, model_name: "demo", created_at: new Date().toISOString() };
    return request<IncidentDiagnosis>(`/projects/${projectId}/incidents/${incidentId}/diagnosis`, { method:"PATCH", body:JSON.stringify({ howsolved }) });
  },
};
