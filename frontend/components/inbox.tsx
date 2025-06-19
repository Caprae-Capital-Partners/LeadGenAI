"use client";

import { useState } from "react";
import { MailOpen, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InboxMessage {
  id: number;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  type?: string;
}

const hardcodedMessages: InboxMessage[] = [
  {
    id: 1,
    title: "🚀 Patch 1.2.0 — Enrichment Speed Boost",
    body: "Improved enrichment backend response time by 40%. Scraping now streams results incrementally.",
    is_read: false,
    type: "patch",
    created_at: "2025-06-18T12:00:00Z",
  },
  {
    id: 2,
    title: "🔒 Security Fixes in Subscription Logic",
    body: "Resolved an edge case where student subscription details weren't loading. Enhanced CORS logic on `/api/auth`.",
    is_read: false,
    type: "patch",
    created_at: "2025-06-17T17:30:00Z",
  },
  {
    id: 3,
    title: "📬 Inbox Feature Launched!",
    body: "All patch notes and important updates will now appear in your profile dropdown → Inbox.",
    is_read: false,
    type: "announcement",
    created_at: "2025-06-17T08:12:00Z",
  }
];

export default function Inbox() {
  const [messages, setMessages] = useState<InboxMessage[]>(hardcodedMessages);

  const markAsRead = (id: number) => {
    setMessages((msgs) =>
      msgs.map((msg) => (msg.id === id ? { ...msg, is_read: true } : msg))
    );
  };

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center text-muted-foreground py-10">
        <MailOpen className="h-10 w-10 mb-2" />
        <p>No messages in your inbox.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`border p-4 rounded-lg ${
            msg.is_read ? "bg-muted" : "bg-card"
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">{msg.title}</h3>
            {!msg.is_read && (
              <Button
                size="sm"
                variant="outline"
                className="text-sm"
                onClick={() => markAsRead(msg.id)}
              >
                Mark as read
              </Button>
            )}
          </div>
          <p className="text-sm text-muted-foreground mb-2">{msg.body}</p>
          <p className="text-xs text-gray-500 italic">
            {new Date(msg.created_at).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}
