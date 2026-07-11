'use client';

import { FormEvent, useEffect, useState } from 'react';

type Employee = {
  name?: string; job_title?: string; department?: string; emp_code?: string;
};

type AuthState = 'loading' | 'guest' | 'authenticated';

export function HrAgentApp() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [isHr, setIsHr] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => { void loadSession(); }, []);

  async function loadSession() {
    try {
      const r = await fetch('/backend/auth/me', { method: 'GET', credentials: 'include', cache: 'no-store' });
      if (!r.ok) { setAuthState('guest'); return; }
      const d = await r.json();
      if (!d.authenticated) { setAuthState('guest'); return; }
      setEmployee(d.employee || null);
      setIsHr(Boolean(d.is_hr));
      setAuthState('authenticated');
    } catch { setAuthState('guest'); }
  }

  async function handleLogin(e: FormEvent<HTMLFormElement>) {
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
      setIsHr(Boolean(d.is_hr));
      setAuthState('authenticated');
      setShowLoginModal(false);
      setLoginForm({ username: '', password: '' });
    } catch { setLoginError('Unable to reach the backend.'); }
    finally { setIsLoggingIn(false); }
  }

  async function handleLogout() {
    await fetch('/backend/auth/logout', { method: 'POST', credentials: 'include' });
    setEmployee(null); setIsHr(false); setAuthState('guest');
  }

  const statusLabel = isHr ? 'HR mode' : 'Employee';

  if (authState === 'loading') {
    return (
      <div className="flex h-screen bg-black text-gray-100">
        <aside className="w-64 border-r border-gray-800 p-5">
          <p className="text-sm font-semibold">JMR HR Portal</p>
        </aside>
        <main className="flex-1 flex items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </main>
      </div>
    );
  }

  if (authState === 'guest') {
    return (
      <div className="flex h-screen bg-black text-gray-100">
        <aside className="w-64 border-r border-gray-800 p-5 flex flex-col gap-6">
          <p className="text-sm font-semibold">JMR HR Portal</p>
        </aside>
        <main className="flex-1 flex flex-col">
          <div className="flex justify-end px-6 py-3 border-b border-gray-800">
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500 border border-gray-700 rounded-full px-3 py-1.5">Sign in required</span>
              <button onClick={() => setShowLoginModal(true)} className="text-xs border border-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-800 transition">Sign in</button>
            </div>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center -mt-16">
              <h1 className="text-3xl font-bold tracking-tight mb-3">JMR HR Portal</h1>
              <p className="text-gray-500 text-sm">Sign in with your HRMS credentials to access the portal.</p>
            </div>
          </div>
        </main>

        {showLoginModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/60" onClick={() => setShowLoginModal(false)} />
            <form onSubmit={handleLogin} className="relative w-full max-w-sm bg-gray-900 border border-gray-700 rounded-2xl p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Sign in</h2>
                <button type="button" onClick={() => setShowLoginModal(false)} className="text-gray-400 text-2xl leading-none hover:text-white">&times;</button>
              </div>
              <p className="text-sm text-gray-400">Use your existing HRMS employee credentials.</p>
              <input type="text" value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                placeholder="Username" autoComplete="username" required
                className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-sm outline-none focus:border-gray-500 transition" />
              <input type="password" value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                placeholder="Password" autoComplete="current-password" required
                className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-sm outline-none focus:border-gray-500 transition" />
              {loginError && <p className="text-red-400 text-xs">{loginError}</p>}
              <button type="submit" disabled={isLoggingIn}
                className="w-full py-2.5 rounded-xl bg-white text-black text-sm font-semibold hover:bg-gray-200 disabled:opacity-50 transition">
                {isLoggingIn ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-black text-gray-100">
      <aside className="w-64 border-r border-gray-800 p-5 flex flex-col gap-6">
        <p className="text-sm font-semibold">JMR HR Portal</p>
        <div>
          <a href="/chat" className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm bg-gray-800 hover:bg-gray-700 transition">
            <span className="text-gray-400">#</span>
            <span>HR Assistant</span>
          </a>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-3 px-2">
          <div className="w-7 h-7 rounded-full bg-amber-500 text-black flex items-center justify-center text-xs font-bold">
            {(employee?.name || 'E').slice(0, 1).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-medium">{employee?.name || 'Employee'}</p>
            <p className="text-[11px] text-gray-500">{statusLabel}</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
          <div>
            <p className="text-[11px] text-gray-500">Signed in as</p>
            <p className="text-sm font-semibold">{employee?.name || 'Employee'}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 border border-gray-700 rounded-full px-3 py-1.5">{statusLabel}</span>
            <button onClick={handleLogout} className="text-xs border border-gray-600 rounded-full px-3 py-1.5 hover:bg-gray-800 transition">Sign out</button>
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center">
          <div className="text-center -mt-16 space-y-4">
            <h1 className="text-2xl font-bold">Welcome{employee?.name ? `, ${employee.name}` : ''}</h1>
            {employee?.emp_code && <p className="text-sm text-gray-400">Employee Code: {employee.emp_code}</p>}
            {employee?.department && <p className="text-sm text-gray-400">Department: {employee.department}</p>}
            {employee?.job_title && <p className="text-sm text-gray-400">Designation: {employee.job_title}</p>}
            <a href="/chat" className="inline-block mt-4 px-6 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-500 transition">
              Open HR Assistant
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
