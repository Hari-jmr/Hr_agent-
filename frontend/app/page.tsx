'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Bot,
  Link,
  ChevronDown,
  Check,
  Copy,
  Square,
  ArrowUp,
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

interface Citation {
  document_id: string;
  document_name: string;
  page_number?: number;
  chunk_id: string;
  content_preview: string;
  confidence_score: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
  isStreaming?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: string;
}

const STORAGE_KEY = 'hr-agent-chat-history';

function useHydrationSafeTimestamp(dateStr: string): string {
  const [timestamp, setTimestamp] = useState('');
  useEffect(() => {
    setTimestamp(new Date(dateStr).toLocaleTimeString());
  }, [dateStr]);
  return timestamp;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function loadSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions: ChatSession[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function generateId() {
  return `chat_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function getFirstUserQuestion(messages: ChatMessage[]): string {
  const first = messages.find((m) => m.role === 'user');
  return first ? first.content.slice(0, 40) + (first.content.length > 40 ? 'ΓÇª' : '') : 'New Chat';
}

/* ------------------------------------------------------------------ */
/*  UI Components                                                     */
/* ------------------------------------------------------------------ */

const UserMessage = ({ message }: { message: ChatMessage }) => {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%]">
        <div className="rounded-3xl bg-accent px-5 py-3">
          <p className="whitespace-pre-wrap text-sm text-foreground">{message.content}</p>
        </div>
      </div>
    </div>
  );
};

const AssistantMessage = ({ message, isStreaming }: { message: ChatMessage; isStreaming?: boolean }) => {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const timestamp = useHydrationSafeTimestamp(message.timestamp);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  return (
    <div className="max-w-none">
      {/* Answer content */}
      <div className="text-[0.9rem] leading-relaxed text-foreground/90">
        {message.content ? (
          <div className="markdown-content">
            <Markdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal space-y-1">{children}</ol>,
                ul: ({ children }) => <ul className="mb-2 ml-4 list-disc space-y-1">{children}</ul>,
                li: ({ children }) => <li className="pl-1">{children}</li>,
                h1: ({ children }) => <h1 className="mb-2 text-lg font-semibold text-foreground">{children}</h1>,
                h2: ({ children }) => <h2 className="mb-2 text-base font-semibold text-foreground">{children}</h2>,
                h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold text-foreground">{children}</h3>,
                code: ({ children }) => (
                  <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono text-foreground/80">{children}</code>
                ),
                pre: ({ children }) => (
                  <pre className="mb-2 overflow-x-auto rounded-lg bg-muted p-3 text-xs">{children}</pre>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="mb-2 border-l-2 border-primary/30 pl-3 text-muted-foreground italic">
                    {children}
                  </blockquote>
                ),
                a: ({ children, href }) => (
                  <a href={href} className="text-primary underline underline-offset-2 hover:text-primary/80">
                    {children}
                  </a>
                ),
              }}
            >
              {message.content}
            </Markdown>
          </div>
        ) : isStreaming ? (
          <div className="flex gap-1">
            <span className="size-2 rounded-full bg-muted-foreground/40 animate-pulse" />
            <span className="size-2 rounded-full bg-muted-foreground/40 animate-pulse delay-100" />
            <span className="size-2 rounded-full bg-muted-foreground/40 animate-pulse delay-200" />
          </div>
        ) : null}
      </div>

      {/* Citations / Sources */}
      {message.citations && message.citations.length > 0 && !isStreaming && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setSourcesOpen((prev) => !prev)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground/70 transition-colors hover:text-muted-foreground"
          >
            <Link className="size-3.5" />
            <span>Sources ({message.citations.length})</span>
            <ChevronDown className={cn('size-3 transition-transform', sourcesOpen && 'rotate-180')} />
          </button>
          {sourcesOpen && (
            <div className="mt-2 space-y-1.5 rounded-lg border border-border/40 bg-muted/20 p-3">
              {message.citations.map((citation, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md px-2 py-1.5 text-xs">
                  <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[9px] font-bold text-primary">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate font-medium text-foreground/90">{citation.document_name}</p>
                      <span className="shrink-0 rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-medium text-primary">
                        {Math.round(citation.confidence_score * 100)}% match
                      </span>
                    </div>
                    {citation.page_number && (
                      <p className="text-muted-foreground/60">Page {citation.page_number}</p>
                    )}
                    <p className="mt-0.5 line-clamp-2 text-muted-foreground/60">{citation.content_preview}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {!isStreaming && timestamp && (
        <div className="mt-2 flex items-center gap-0.5">
          <button
            onClick={handleCopy}
            className="inline-flex items-center justify-center size-7 rounded-full text-muted-foreground/50 hover:text-muted-foreground hover:bg-accent transition-colors"
            title={copied ? 'Copied!' : 'Copy'}
          >
            {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
          </button>
          <span className="ml-1 text-[11px] text-muted-foreground/50">{timestamp}</span>
        </div>
      )}
    </div>
  );
};

const ChatMessageBubble = ({ message }: { message: ChatMessage }) => {
  if (message.role === 'user') {
    return <UserMessage message={message} />;
  }
  return <AssistantMessage message={message} isStreaming={message.isStreaming} />;
};

/* ------------------------------------------------------------------ */
/*  Chat Input                                                        */
/* ------------------------------------------------------------------ */

const ChatInput = ({ onSubmit, isLoading }: { onSubmit: (question: string) => Promise<void>; isLoading: boolean }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    await onSubmit(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        onSubmit(input);
        setInput('');
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
        }
      }
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl">
      <div className="rounded-2xl border border-border/60 bg-muted/40 px-3 pb-2 pt-2">
        <textarea
          ref={textareaRef}
          className="w-full resize-none bg-transparent px-1 text-sm leading-6 outline-none placeholder:text-muted-foreground/70"
          placeholder="Ask about HR policies..."
          rows={1}
          value={input}
          onChange={(e) => { setInput(e.target.value); adjustHeight(); }}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          style={{ maxHeight: '200px' }}
        />
        <div className="mt-1 flex items-center gap-2">
          <div className="flex-1" />
          {isLoading ? (
            <button
              onClick={() => { /* stop would need abort controller */ }}
              className="inline-flex items-center justify-center size-8 rounded-full bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Square className="size-4 fill-current" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="inline-flex items-center justify-center size-8 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none transition-colors"
            >
              <ArrowUp className="size-4" />
            </button>
          )}
        </div>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground/60">
        HR Agent Bot can make mistakes. Check important info.
      </p>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  Auth                                                              */
/* ------------------------------------------------------------------ */

type AuthState = 'loading' | 'guest' | 'authenticated';
type Employee = { name?: string; emp_code?: string; department?: string; job_title?: string };

/* ------------------------------------------------------------------ */
/*  Main Page                                                         */
/* ------------------------------------------------------------------ */

export default function ChatPage() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* Check session on mount */
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/backend/auth/me', { credentials: 'include', cache: 'no-store' });
        const d = await r.json();
        if (d.authenticated) {
          setEmployee(d.employee || null);
          setAuthState('authenticated');
          const loaded = loadSessions();
          setSessions(loaded);
          if (loaded.length > 0) {
            const mostRecent = loaded.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())[0];
            setActiveSessionId(mostRecent.id);
            setMessages(mostRecent.messages);
          }
        } else {
          setAuthState('guest');
        }
      } catch {
        setAuthState('guest');
      }
    })();
  }, []);

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError('');
    try {
      const r = await fetch('/backend/auth/login', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm),
      });
      const d = await r.json();
      if (!r.ok) { setLoginError(d.error || 'Unable to sign in.'); return; }
      setEmployee(d.employee || null);
      setAuthState('authenticated');
      setLoginForm({ username: '', password: '' });
    } catch { setLoginError('Unable to reach the backend.'); }
    finally { setIsLoggingIn(false); }
  }

  async function handleLogout() {
    await fetch('/backend/auth/logout', { method: 'POST', credentials: 'include' });
    setEmployee(null); setAuthState('guest');
  }

  /* Save to localStorage whenever sessions change */
  useEffect(() => {
    if (authState === 'authenticated') saveSessions(sessions);
  }, [sessions, authState]);

  /* Scroll to bottom */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* Create a brand-new chat */
  const startNewChat = useCallback(() => {
    const newSession: ChatSession = {
      id: generateId(),
      title: 'New Chat',
      messages: [],
      updatedAt: new Date().toISOString(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setMessages([]);
  }, []);

  /* Delete a session */
  const deleteSession = useCallback((sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      if (activeSessionId === sessionId) {
        if (filtered.length > 0) {
          setActiveSessionId(filtered[0].id);
          setMessages(filtered[0].messages);
        } else {
          setActiveSessionId('');
          setMessages([]);
        }
      }
      return filtered;
    });
  }, [activeSessionId]);

  /* Switch to an existing session */
  const switchSession = useCallback((sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setActiveSessionId(sessionId);
      setMessages(session.messages);
    }
  }, [sessions]);

  /* Persist current messages into the active session */
  const persistMessages = useCallback((updatedMessages: ChatMessage[]) => {
    setMessages(updatedMessages);
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId
          ? { ...s, messages: updatedMessages, title: getFirstUserQuestion(updatedMessages), updatedAt: new Date().toISOString() }
          : s
      )
    );
  }, [activeSessionId]);

  /* ---------------------------------------------------------------- */
  /*  Query handler                                                   */
  /* ---------------------------------------------------------------- */

  const handleQuery = async (question: string) => {
    /* Auto-start a new session if none exists */
    let currentSessionId = activeSessionId;
    if (!currentSessionId || sessions.length === 0) {
      const newId = generateId();
      const newSession: ChatSession = {
        id: newId,
        title: question.slice(0, 40) + (question.length > 40 ? 'ΓÇª' : ''),
        messages: [],
        updatedAt: new Date().toISOString(),
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newId);
      currentSessionId = newId;
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    const nextMessages = [...messages, userMessage];
    persistMessages(nextMessages);
    setIsLoading(true);

    try {
      const assistantMessageId = `msg_${Date.now() + 1}`;
      let assistantContent = '';
      let citations: Citation[] = [];

      const streamingMessages: ChatMessage[] = [
        ...nextMessages,
        {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          citations: [],
          isStreaming: true,
          timestamp: new Date().toISOString(),
        },
      ];
      persistMessages(streamingMessages);

      const conversationHistory = nextMessages.map((m) => ({
        role: m.role,
        content: m.content,
        citations: m.citations,
        timestamp: m.timestamp,
      }));

      const response = await fetch('http://localhost:8001/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          conversation_history: conversationHistory,
          session_id: currentSessionId,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', response.status, errorText);
        throw new Error(`Query failed: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n').filter((line) => line.trim());

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.type === 'start') {
              citations = data.citations || [];
            } else if (data.type === 'chunk') {
              assistantContent += data.content;
              const updated = streamingMessages.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, content: assistantContent, citations } : msg
              );
              persistMessages(updated);
            } else if (data.type === 'end') {
              const final = streamingMessages.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, content: assistantContent, isStreaming: false, citations } : msg
              );
              persistMessages(final);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessages = [
        ...nextMessages,
        {
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ];
      persistMessages(errorMessages);
    } finally {
      setIsLoading(false);
    }
  };

  const isEmpty = messages.length === 0;

  /* ---------------------------------------------------------------- */
  /*  Render                                                          */
  /* ---------------------------------------------------------------- */

  if (authState === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
            <Bot className="size-6 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (authState === 'guest') {
    return (
      <div className="flex h-screen items-center justify-center bg-background p-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-primary/10">
              <Bot className="size-7 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">JMR HR Portal</h1>
            <p className="mt-1 text-sm text-muted-foreground">Sign in with your HRMS credentials</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text" value={loginForm.username}
              onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
              placeholder="Username" autoComplete="username" required
              className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm outline-none focus:border-ring transition"
            />
            <input
              type="password" value={loginForm.password}
              onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              placeholder="Password" autoComplete="current-password" required
              className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm outline-none focus:border-ring transition"
            />
            {loginError && <p className="text-sm text-destructive">{loginError}</p>}
            <button
              type="submit" disabled={isLoggingIn}
              className="w-full rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition"
            >
              {isLoggingIn ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r border-border bg-card transition-all duration-200',
          sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
        )}
      >
        <div className="flex items-center justify-between px-3 py-3">
          <button
            onClick={startNewChat}
            className="flex flex-1 items-center gap-2 rounded-lg border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <Plus className="size-3.5" />
            New Chat
          </button>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-2 inline-flex items-center justify-center size-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <PanelLeftClose className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2">
          {sessions.length === 0 ? (
            <p className="px-2 text-xs text-muted-foreground">No chat history yet</p>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => switchSession(session.id)}
                  className={cn(
                    'group flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-xs transition-colors',
                    session.id === activeSessionId
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
                  )}
                >
                  <MessageSquare className="size-3.5 shrink-0" />
                  <span className="flex-1 truncate">{session.title}</span>
                  <button
                    onClick={(e) => deleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 inline-flex items-center justify-center size-6 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
                  >
                    <Trash2 className="size-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="border-b border-border bg-card px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-center justify-between">
            <div className="flex items-center gap-2">
              {!sidebarOpen && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="inline-flex items-center justify-center size-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                >
                  <PanelLeftOpen className="size-4" />
                </button>
              )}
              <div className="flex size-8 items-center justify-center rounded-full bg-primary/10">
                <Bot className="size-4 text-primary" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-foreground">HR Agent Bot</h1>
                <p className="text-[11px] text-muted-foreground">Powered by OpenRouter + pgvector</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {employee?.name && (
                <span className="text-xs text-muted-foreground">{employee.name}</span>
              )}
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1 rounded-lg border border-input bg-background px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </header>

        {/* Messages or Empty State */}
        <main className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {isEmpty ? (
              <div className="flex h-full flex-col items-center justify-center py-20">
                <div className="text-center">
                  <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
                    <Bot className="size-6 text-muted-foreground" />
                  </div>
                  <h1 className="text-2xl font-medium text-foreground">What can I help with?</h1>
                  <p className="mt-2 text-sm text-muted-foreground">Ask about HR policies, leave, benefits, or procedures.</p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessageBubble key={message.id} message={message} />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input */}
        <footer className="px-4 pb-4 pt-2">
          <ChatInput onSubmit={handleQuery} isLoading={isLoading} />
        </footer>
      </div>
    </div>
  );
}
