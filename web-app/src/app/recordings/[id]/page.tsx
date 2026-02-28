"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  fetchMeeting,
  fetchSummary,
  fetchTranscript,
  fetchRecording,
  type Meeting,
  type Summary,
  type TranscriptSegment,
} from "@/lib/api";

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function RecordingDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const [recording, setRecording] = useState<{ mixed_audio_url: string | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchMeeting(id),
      fetchSummary(id),
      fetchTranscript(id),
      fetchRecording(id),
    ])
      .then(([m, s, t, r]) => {
        if (!cancelled) {
          setMeeting(m);
          setSummary(s);
          setTranscript(t.segments);
          setRecording(r);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">Loading...</p>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-red-600">{error || "Meeting not found"}</p>
        <Link href="/" className="text-slate-600 hover:underline">
          ← Back to recordings
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-slate-800">
            ← Back
          </Link>
          <h1 className="text-xl font-semibold text-slate-800">
            {meeting.title} · {meeting.call_date}
          </h1>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-6 text-sm text-slate-600">
          Participants: {meeting.participants.join(", ")} · Duration: {meeting.duration_minutes} min
        </div>

        {summary && (
          <section className="mb-8">
            <h2 className="mb-2 text-lg font-semibold text-slate-800">Summary</h2>
            <p className="whitespace-pre-wrap text-slate-700">{summary.summary}</p>
          </section>
        )}

        <div className="grid gap-8 lg:grid-cols-2">
          {summary && summary.action_items.length > 0 && (
            <section>
              <h2 className="mb-2 text-lg font-semibold text-slate-800">Action Items</h2>
              <ul className="list-inside list-disc space-y-1 text-slate-700">
                {summary.action_items.map((a, i) => (
                  <li key={i}>
                    {a.task}
                    {a.assignee && ` (${a.assignee})`}
                    {a.due && ` — Due ${a.due}`}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {summary && summary.decisions.length > 0 && (
            <section>
              <h2 className="mb-2 text-lg font-semibold text-slate-800">Decisions</h2>
              <ul className="list-inside list-disc space-y-1 text-slate-700">
                {summary.decisions.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {transcript.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-2 text-lg font-semibold text-slate-800">Transcript</h2>
            <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
              {transcript.map((seg, i) => (
                <div key={i} className="text-sm">
                  <span className="font-medium text-slate-600">
                    [{formatTime(seg.start_time)}] {seg.speaker}:
                  </span>{" "}
                  <span className="text-slate-700">{seg.text}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {recording?.mixed_audio_url && (
          <section className="mt-8">
            <h2 className="mb-2 text-lg font-semibold text-slate-800">Recording</h2>
            <audio controls className="w-full" src={recording.mixed_audio_url}>
              Your browser does not support audio.
            </audio>
          </section>
        )}

        {recording && !recording.mixed_audio_url && (
          <section className="mt-8 rounded-lg border border-slate-200 bg-slate-100 p-4 text-sm text-slate-600">
            Audio playback will be available once recordings are stored. The pipeline saves audio to
            object storage and provides signed URLs here.
          </section>
        )}
      </main>
    </div>
  );
}
