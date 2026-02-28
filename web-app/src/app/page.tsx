"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchRecordings, type Recording } from "@/lib/api";

function formatDate(d: string) {
  return new Date(d + "T12:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function Home() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState("");
  const [participant, setParticipant] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchRecordings(date || undefined, participant || undefined)
      .then((data) => {
        if (!cancelled) setRecordings(data.recordings);
      })
      .catch(() => {
        if (!cancelled) setRecordings([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [date, participant]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <h1 className="text-xl font-semibold text-slate-800">AI Meeting Notes</h1>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-8">
        <div className="mb-6 flex flex-wrap gap-4">
          <div>
            <label className="mb-1 block text-sm text-slate-600">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">Participant</label>
            <input
              type="text"
              placeholder="Filter by name"
              value={participant}
              onChange={(e) => setParticipant(e.target.value)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {loading ? (
          <p className="text-slate-500">Loading recordings...</p>
        ) : recordings.length === 0 ? (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-slate-500">
            No recordings found. Recordings will appear here once the bot joins meetings and the
            pipeline processes them.
          </div>
        ) : (
          <div className="space-y-4">
            {recordings.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="font-medium text-slate-800">{r.title}</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {formatDate(r.call_date)} · {r.duration_minutes} min
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {r.participants.join(", ")}
                    </p>
                  </div>
                  <Link
                    href={`/recordings/${r.meeting_id}`}
                    className="shrink-0 rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
                  >
                    View Notes
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
