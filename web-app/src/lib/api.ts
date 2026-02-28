const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Recording = {
  id: string;
  meeting_id: string;
  title: string;
  call_date: string;
  duration_minutes: number;
  participants: string[];
  status: string;
};

export type Meeting = {
  id: string;
  zoom_meeting_id: string;
  title: string;
  start_time: string;
  end_time: string;
  call_date: string;
  duration_minutes: number;
  host_name: string;
  participants: string[];
  status: string;
};

export type Summary = {
  meeting_id: string;
  summary: string;
  action_items: { task: string; assignee?: string; due?: string }[];
  decisions: string[];
  risks: string[];
  next_steps: string[];
};

export type TranscriptSegment = {
  speaker: string;
  start_time: number;
  end_time: number;
  text: string;
};

export async function fetchRecordings(
  date?: string,
  participant?: string
): Promise<{ recordings: Recording[] }> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (participant) params.set("participant", participant);
  const res = await fetch(`${API_URL}/recordings?${params}`);
  if (!res.ok) throw new Error("Failed to fetch recordings");
  return res.json();
}

export async function fetchMeeting(id: string): Promise<Meeting> {
  const res = await fetch(`${API_URL}/meetings/${id}`);
  if (!res.ok) throw new Error("Failed to fetch meeting");
  return res.json();
}

export async function fetchSummary(id: string): Promise<Summary> {
  const res = await fetch(`${API_URL}/meetings/${id}/summary`);
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function fetchTranscript(id: string): Promise<{
  meeting_id: string;
  segments: TranscriptSegment[];
}> {
  const res = await fetch(`${API_URL}/meetings/${id}/transcript`);
  if (!res.ok) throw new Error("Failed to fetch transcript");
  return res.json();
}

export async function fetchRecording(id: string): Promise<{
  meeting_id: string;
  call_date: string;
  mixed_audio_url: string | null;
  participant_audio: Record<string, string | null>;
  duration_seconds: number;
}> {
  const res = await fetch(`${API_URL}/meetings/${id}/recording`);
  if (!res.ok) throw new Error("Failed to fetch recording");
  return res.json();
}
