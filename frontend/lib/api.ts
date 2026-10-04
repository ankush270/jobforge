/**
 * JobForge API client — typed wrapper for all backend endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('jobforge_token');
}

export function hasToken(): boolean {
  return !!getToken();
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;
  const token = getToken();

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${path}`, config);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, error.detail || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, error.detail || res.statusText);
  }

  return res.json();
}

// ── Auth ────────────────────────────────────────────
export const auth = {
  register: (data: { email: string; name?: string; password: string }) =>
    request<{ access_token: string; user: User }>('/api/auth/register', { method: 'POST', body: data }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; user: User }>('/api/auth/login', { method: 'POST', body: data }),

  me: () => request<User>('/api/auth/me'),
};

// ── Resumes ─────────────────────────────────────────
export const resumes = {
  upload: (file: File) =>
    uploadFile<{ resume: Resume; career_profile: CareerProfile | null }>('/api/resumes/upload', file),

  list: () => request<Resume[]>('/api/resumes/'),

  get: (id: string) => request<Resume>(`/api/resumes/${id}`),

  pdfUrl: (id: string) => `${API_BASE}/api/resumes/${id}/pdf`,
  latexUrl: (id: string) => `${API_BASE}/api/resumes/${id}/latex`,
  latexPdfUrl: (id: string) => `${API_BASE}/api/resumes/${id}/latex-pdf`,

  update: (id: string, data: Partial<Resume>) =>
    request<Resume>(`/api/resumes/${id}`, { method: 'PATCH', body: data }),

  delete: (id: string) =>
    request<void>(`/api/resumes/${id}`, { method: 'DELETE' }),
};

// ── Jobs ────────────────────────────────────────────
export const jobs = {
  list: (params?: { page?: number; search?: string; platform?: string; location?: string }) => {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.search) qs.set('search', params.search);
    if (params?.platform) qs.set('platform', params.platform);
    if (params?.location) qs.set('location', params.location);
    return request<{ jobs: Job[]; total: number; page: number; page_size: number }>(`/api/jobs/?${qs}`);
  },

  get: (id: string) => request<Job>(`/api/jobs/${id}`),

  create: (data: JobCreate) =>
    request<Job>('/api/jobs/', { method: 'POST', body: data }),

  clip: (data: JobClipRequest) =>
    request<Job>('/api/jobs/clip', { method: 'POST', body: data }),

  scrape: (data: { platforms: string[]; search_query: string; location?: string; results_wanted?: number }) =>
    request<{ message: string; scraped: number; saved: number }>('/api/jobs/scrape', { method: 'POST', body: data }),
};

// ── Evaluations ─────────────────────────────────────
export const evaluations = {
  atsScore: (resumeId: string, jobId: string) =>
    request<ATSScore>(`/api/evaluations/ats-score?resume_id=${resumeId}&job_id=${jobId}`, { method: 'POST' }),

  tailor: (data: { resume_id: string; job_id: string }) =>
    request<TailoredResume>('/api/evaluations/tailor', { method: 'POST', body: data }),

  tailoredPdfUrl: (tailoredId: string) => `${API_BASE}/api/evaluations/tailored/${tailoredId}/pdf`,
  tailoredLatexUrl: (tailoredId: string) => `${API_BASE}/api/evaluations/tailored/${tailoredId}/latex`,
  tailoredLatexPdfUrl: (tailoredId: string) => `${API_BASE}/api/evaluations/tailored/${tailoredId}/latex-pdf`,

  upskillGap: (resumeId: string, jobId: string) =>
    request<UpskillResult>(`/api/evaluations/upskill-gap?resume_id=${resumeId}&job_id=${jobId}`, { method: 'POST' }),

  jobEval: (jobId: string) =>
    request<JobEvaluationResult>(`/api/evaluations/job/${jobId}`),
};

// ── Applications ────────────────────────────────────
export const applications = {
  board: () => request<KanbanBoard>('/api/applications/board'),

  create: (data: { job_id: string; status?: string }) =>
    request<Application>('/api/applications/', { method: 'POST', body: data }),

  update: (id: string, data: Partial<Application>) =>
    request<Application>(`/api/applications/${id}`, { method: 'PATCH', body: data }),

  stats: () => request<FunnelStats>('/api/applications/stats'),

  delete: (id: string) =>
    request<void>(`/api/applications/${id}`, { method: 'DELETE' }),
};

// ── Cover Letters ───────────────────────────────────
export const coverLetters = {
  generate: (data: { job_id: string; resume_id?: string; mode?: 'cover_letter' | 'email' }) =>
    request<CoverLetter>('/api/cover-letters/generate', { method: 'POST', body: data }),
  list: () => request<CoverLetter[]>('/api/cover-letters/'),
  get: (id: string) => request<CoverLetter>(`/api/cover-letters/${id}`),
  delete: (id: string) => request<void>(`/api/cover-letters/${id}`, { method: 'DELETE' }),
};

// ── Interviews ──────────────────────────────────────
export const interviews = {
  prep: (data: { job_id: string; resume_id?: string; application_id?: string; round?: number; interview_type?: string }) =>
    request<Interview>('/api/interviews/prep', { method: 'POST', body: data }),
  list: () => request<Interview[]>('/api/interviews/'),
  get: (id: string) => request<Interview>(`/api/interviews/${id}`),
  update: (id: string, data: Partial<Interview>) =>
    request<Interview>(`/api/interviews/${id}`, { method: 'PATCH', body: data }),
  delete: (id: string) => request<void>(`/api/interviews/${id}`, { method: 'DELETE' }),
};

// ── Salaries ────────────────────────────────────────
export const salaries = {
  benchmark: (params: { role: string; experience_yrs?: number; location?: string; currency?: string }) => {
    const qs = new URLSearchParams({ role: params.role });
    if (params.experience_yrs) qs.set('experience_yrs', String(params.experience_yrs));
    if (params.location) qs.set('location', params.location);
    if (params.currency) qs.set('currency', params.currency);
    return request<SalaryBenchmarkResult>(`/api/salaries/benchmark?${qs}`);
  },
  analyzeGap: (data: { offered_salary: number; role: string; experience_yrs?: number; location?: string; currency?: string }) =>
    request<{ benchmark: SalaryBenchmarkResult; analysis: Record<string, unknown> }>('/api/salaries/analyze-gap', { method: 'POST', body: data }),
  negotiate: (data: { company_name: string; role: string; current_offer: number; target_salary: number; currency?: string; key_strengths?: string[] }) =>
    request<{ negotiation_script: string; suggested_target: number; currency: string }>('/api/salaries/negotiate', { method: 'POST', body: data }),
};

// ── Companies ───────────────────────────────────────
export const companies = {
  list: () => request<Array<{ id: string; name: string; slug: string; tier: string | null }>>('/api/companies/'),
  intel: (identifier: string) => request<CompanyIntelResult>(`/api/companies/${identifier}/intel`),
};

// ── QA Bank ─────────────────────────────────────────
export const qaBank = {
  list: () => request<QABankEntry[]>('/api/qa-bank/'),
  create: (data: { question_key: string; answer: string; context?: string }) =>
    request<QABankEntry>('/api/qa-bank/', { method: 'POST', body: data }),
  generate: (data: { question: string; job_id?: string; resume_id?: string; save_to_bank?: boolean }) =>
    request<{ question: string; answer: string; saved: boolean }>('/api/qa-bank/generate', { method: 'POST', body: data }),
  replyDraft: (data: { incoming_email: string; intent?: string }) =>
    request<{ intent: string; email_draft: string }>('/api/qa-bank/reply-draft', { method: 'POST', body: data }),
  delete: (id: string) => request<void>(`/api/qa-bank/${id}`, { method: 'DELETE' }),
};

export const contacts = {
  list: (companyId?: string) =>
    request<Contact[]>(`/api/contacts/${companyId ? `?company_id=${companyId}` : ''}`),
  create: (data: { name: string; company_id?: string; title?: string; email?: string; linkedin_url?: string; notes?: string }) =>
    request<Contact>('/api/contacts/', { method: 'POST', body: data }),
  draftPitch: (data: { contact_name: string; contact_title?: string; company_name: string; target_role: string; candidate_skills?: string[] }) =>
    request<{ pitch_text: string; contact_name: string; company_name: string }>('/api/contacts/draft-pitch', { method: 'POST', body: data }),
  delete: (id: string) => request<void>(`/api/contacts/${id}`, { method: 'DELETE' }),
};

// ── Health ──────────────────────────────────────────
export const health = {
  check: () => request<{ status: string; version: string }>('/api/health'),
};

// ── Types ───────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  content: Record<string, unknown>;
  content_md: string | null;
  is_master: boolean;
  is_default: boolean;
  parent_id: string | null;
  filename: string | null;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

export interface CareerProfile {
  id: string;
  user_id: string;
  profile_json: Record<string, unknown>;
  raw_text: string | null;
}

export interface Job {
  id: string;
  company_id: string | null;
  canonical_key: string;
  title: string;
  description: string;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  job_type: string | null;
  remote_type: string | null;
  source_platform: string;
  source_url: string | null;
  posted_at: string | null;
  is_ghost: boolean;
  ghost_signals: unknown[];
  is_alive: boolean;
  keywords: Record<string, unknown>;
  enrichment: Record<string, unknown>;
  created_at: string;
  company: { name: string; slug: string; tier: string | null } | null;
}

export interface JobCreate {
  title: string;
  company_name: string;
  description: string;
  location?: string;
  source_platform?: string;
  source_url?: string;
}

export interface JobClipRequest {
  title: string;
  company_name: string;
  description: string;
  source_url: string;
  source_platform?: string;
}

export interface ATSScore {
  overall_score: number;
  sub_scores: { keyword_match: number; skills_coverage: number; section_completeness: number };
  missing_keywords: string[];
  injectable_keywords: string[];
  recommendations: string[];
}

export interface TailoredResume {
  id: string;
  source_resume_id: string;
  job_id: string;
  content: Record<string, unknown>;
  ats_score: number | null;
  ats_breakdown: Record<string, number> | null;
  missing_keywords: string[] | null;
  recommendations: string[] | null;
  fact_check_status: string;
}

export interface Application {
  id: string;
  job_id: string;
  status: string;
  applied_at: string | null;
  notes: string | null;
  position: number;
  created_at: string;
  job?: Job;
}

export interface KanbanBoard {
  columns: Record<string, Application[]>;
  stats: Record<string, number>;
}

export interface FunnelStats {
  total_applied: number;
  screening: number;
  interviewing: number;
  offers: number;
  rejected: number;
  ghosted: number;
  screen_rate: number | null;
  offer_rate: number | null;
}

export interface CoverLetter {
  id: string;
  user_id: string;
  job_id: string;
  content: string;
  format: string;
  created_at: string;
}

export interface Interview {
  id: string;
  application_id: string;
  round: number;
  interview_type: string | null;
  scheduled_at: string | null;
  prep_notes: {
    predicted_questions?: Array<{ category: string; question: string; why_they_ask: string; key_talking_points: string[] }>;
    star_stories?: Array<{ theme: string; situation: string; task: string; action: string; result: string }>;
    reverse_questions_to_ask?: string[];
    culture_red_flags_to_watch?: string[];
    study_plan?: Array<{ day: number; focus: string }>;
  } | null;
  debrief: string | null;
  outcome: string | null;
  red_flags: string[];
  created_at: string;
}

export interface SalaryBenchmarkResult {
  role: string;
  matched_standard_role: string;
  currency: string;
  p25: number;
  p50_median: number;
  p75: number;
  p90: number;
  experience_adjustment: string;
  location: string;
}

export interface CompanyIntelResult {
  company_id: string;
  name: string;
  slug: string;
  tier: string | null;
  intel: {
    tier?: string;
    overview?: string;
    funding_stage?: string;
    estimated_headcount?: string;
    engineering_culture_rating?: number;
    tech_stack_highlights?: string[];
    culture_positives?: string[];
    potential_red_flags?: string[];
    stability_assessment?: string;
  };
}

export interface QABankEntry {
  id: string;
  user_id: string;
  question_key: string;
  answer: string;
  context: string | null;
  is_default: boolean;
  created_at: string;
}

export interface Contact {
  id: string;
  user_id: string;
  company_id: string | null;
  company_name?: string;
  name: string;
  title: string | null;
  role?: string;
  email: string | null;
  linkedin_url: string | null;
  source: string | null;
  notes: string | null;
  created_at: string;
}

export interface UpskillResult {
  current_fit_score: number;
  projected_fit_score: number;
  critical_skill_gaps: Array<{
    skill: string;
    importance: string;
    reason: string;
  }>;
  proof_of_work_projects: Array<{
    title: string;
    time_estimate: string;
    target_skills_bridged: string[];
    description: string;
    key_architecture_deliverables: string[];
    resume_bullet_preview: string;
  }>;
  recommended_learning_resources: Array<{
    topic: string;
    resource_type: string;
    recommendation: string;
  }>;
}

export interface JobEvaluationResult {
  id: string;
  overall_score: number | null;
  recommendation?: string;
  tier: string | null;
  block_a_role_match?: Record<string, unknown>;
  block_b_cv_fit?: Record<string, unknown>;
  block_c_level_strategy?: Record<string, unknown>;
  block_d_compensation?: Record<string, unknown>;
  block_e_personalization_angle?: Record<string, unknown>;
  block_f_interview_prep?: Record<string, unknown>;
  block_g_legitimacy_check?: Record<string, unknown>;
  block_h_location_auth?: Record<string, unknown>;
  created_at: string;
}

// ── Target Companies ────────────────────────────────
export interface TargetCompany {
  name: string;
  category: string;
  careers_url: string;
  ats_or_portal: string | null;
  locations_in_india: string[];
  status: string;
}

export const targetCompanies = {
  list: (params?: { search?: string; category?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set('search', params.search);
    if (params?.category && params.category !== 'All') q.set('category', params.category);
    const qs = q.toString();
    return request<TargetCompany[]>(`/api/companies/targets${qs ? `?${qs}` : ''}`);
  },

  add: (data: { name: string; careers_url: string; category?: string; locations_in_india?: string[] }) =>
    request<TargetCompany>('/api/companies/targets', { method: 'POST', body: data }),

  remove: (name: string) =>
    request<{ message: string; remaining: number }>(`/api/companies/targets/${encodeURIComponent(name)}`, { method: 'DELETE' }),
};

