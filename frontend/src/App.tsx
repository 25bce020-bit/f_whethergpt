import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import type { User } from './api/types';
import { ApiError } from './api/client';
import { auth } from './api/services';
import { Header, Drawer, ProfileMenu } from './components/Shell';
import { About, AuthPage, ChatPage, Climate, Forecast, Maps, Profile, Settings, Voice } from './pages';
import { startNewChat } from './chatSession';
import { applyTheme, getInitialTheme, type Theme } from './theme';

export type AuthState = { status: 'loading' | 'guest' | 'authenticated'; user: User | null };

export default function App() {
  const [authState, setAuthState] = useState<AuthState>({ status: 'loading', user: null });
  const [drawer, setDrawer] = useState(false);
  const [profile, setProfile] = useState(false);
  const [chatKey, setChatKey] = useState(0);
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme());

  const refresh = async () => {
    try {
      const { user } = await auth.me();
      setAuthState({ status: 'authenticated', user });
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setAuthState({ status: 'guest', user: null });
      else setAuthState({ status: 'guest', user: null });
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const logout = async () => {
    await auth.logout().catch(() => undefined);
    setAuthState({ status: 'guest', user: null });
    setProfile(false);
  };

  const newChat = () => {
    startNewChat();
    setChatKey((key) => key + 1);
  };

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
    applyTheme(newTheme);
  };

  return (
    <div className="app-shell">
      <div className="atmosphere a" />
      <div className="atmosphere b" />
      <Header
        onMenu={() => setDrawer(true)}
        onProfile={() => setProfile((v) => !v)}
        user={authState.user}
      />
      <Drawer
        open={drawer}
        close={() => setDrawer(false)}
        auth={authState}
        onLogout={logout}
        onNewChat={newChat}
        theme={theme}
        onThemeChange={handleThemeChange}
      />
      {profile && (
        <ProfileMenu
          auth={authState}
          close={() => setProfile(false)}
          onLogout={logout}
        />
      )}
      <main>
        <Routes>
          <Route path="/" element={<ChatPage key={chatKey} />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/climate" element={<Climate />} />
          <Route path="/maps" element={<Maps />} />
          <Route path="/voice" element={<Voice />} />
          <Route
            path="/settings"
            element={<Settings theme={theme} onThemeChange={handleThemeChange} />}
          />
          <Route path="/profile" element={<Profile auth={authState} onLogout={logout} />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<AuthPage kind="login" refresh={refresh} />} />
          <Route path="/signup" element={<AuthPage kind="signup" refresh={refresh} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
