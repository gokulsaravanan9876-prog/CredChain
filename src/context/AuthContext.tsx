// ---------------------------------------------------------------------------
// Central auth state. This is the only place the JWT is read/written —
// everything else (routes, pages, api.ts calls) goes through useAuth().
//
// Token storage: localStorage, behind a single key, accessed only here.
// SECURITY TRADEOFF (documented, not hidden): localStorage is readable by
// any JS running on the page, so a successful XSS on this frontend can
// steal the token. An HttpOnly cookie would avoid that, but requires the
// backend to issue/manage a session cookie (Set-Cookie + CORS credentials +
// CSRF protection) which is real additional infrastructure — out of scope
// for this hackathon phase. Two things bound the actual risk here: 1) tokens
// are short-lived (ACCESS_TOKEN_EXPIRE_MINUTES, currently 24h — tune down
// for a real deployment), and 2) this app has no third-party script
// inclusion, which is the usual XSS vector. Revisit if this ever becomes a
// real production deployment rather than a hackathon MVP.
// ---------------------------------------------------------------------------

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { setAuthToken } from '../lib/apiClient'
import { login as loginRequest, register as registerRequest, getCurrentUser, logout as logoutRequest } from '../lib/api'
import type { AuthUser, RegisterPayload } from '../types'

const TOKEN_STORAGE_KEY = 'credchain_token'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<AuthUser>
  register: (payload: RegisterPayload) => Promise<AuthUser>
  logout: () => void
  /** Re-fetches the authenticated user from the backend (e.g. after linking an institution) without a full re-login. */
  refreshUser: () => Promise<AuthUser>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const clearSession = useCallback(() => {
    setAuthToken(null)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setUser(null)
  }, [])

  // On first load: if a token was persisted from a previous session, verify
  // it's still valid via /auth/me before trusting it (proves persistence
  // across refresh — a bad/expired token just drops back to logged-out).
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!stored) {
      setLoading(false)
      return
    }
    setAuthToken(stored)
    getCurrentUser()
      .then(setUser)
      .catch(() => clearSession())
      .finally(() => setLoading(false))
  }, [clearSession])

  // apiClient dispatches this on any 401 response — centralizes "session
  // died mid-app" handling instead of every call site checking for it.
  useEffect(() => {
    const handleUnauthorized = () => clearSession()
    window.addEventListener('credchain:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('credchain:unauthorized', handleUnauthorized)
  }, [clearSession])

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password)
    localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token)
    setAuthToken(result.access_token)
    setUser(result.user)
    return result.user
  }, [])

  // Registration returns a real token (backend logs the new account straight
  // in, same as login) — reuses the exact same session-establishing steps.
  const register = useCallback(async (payload: RegisterPayload) => {
    const result = await registerRequest(payload)
    localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token)
    setAuthToken(result.access_token)
    setUser(result.user)
    return result.user
  }, [])

  const refreshUser = useCallback(async () => {
    const fresh = await getCurrentUser()
    setUser(fresh)
    return fresh
  }, [])

  const logout = useCallback(() => {
    // Stateless JWT — the backend call just confirms the token was valid;
    // the client discarding it (clearSession) is what actually logs out.
    logoutRequest().catch(() => {})
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
