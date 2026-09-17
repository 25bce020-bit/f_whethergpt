import { useEffect, useRef } from 'react';
import { Link, NavLink } from 'react-router-dom';
import {
  CloudSun,
  HistoryIcon,
  Info,
  LogIn,
  LogOut,
  MapIcon,
  Menu,
  MessageSquare,
  Moon,
  Plus,
  Settings,
  Sun,
  UserRound,
  Volume2,
  X,
} from './icons';
import type { AuthState } from '../App';
import type { Theme } from '../theme';

export function Header({
  onMenu,
  onProfile,
  user,
}: {
  onMenu: () => void;
  onProfile: () => void;
  user: AuthState['user'];
}) {
  return (
    <header className="topbar glass">
      <button
        className="icon-button"
        type="button"
        aria-label="Open navigation menu"
        onClick={onMenu}
      >
        <Menu />
      </button>

      <Link className="brand" to="/" aria-label="WeatherGPT Home">
        <span className="brand-mark">
          <CloudSun />
        </span>
        <span className="brand-text">WeatherGPT</span>
      </Link>

      <button
        className="avatar-btn"
        type="button"
        aria-label="Open profile menu"
        aria-haspopup="true"
        onClick={onProfile}
      >
        <span className="avatar-disc">
          {user?.name ? user.name[0].toUpperCase() : <UserRound />}
        </span>
      </button>
    </header>
  );
}

export function Drawer({
  open,
  close,
  auth: currentAuth,
  onLogout,
  onNewChat,
  theme,
  onThemeChange,
}: {
  open: boolean;
  close: () => void;
  auth: AuthState;
  onLogout: () => void;
  onNewChat: () => void;
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
}) {
  const drawerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) close();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, close]);

  return (
    <div className={`drawer-wrap ${open ? 'open' : ''}`} aria-hidden={!open}>
      <button
        className="scrim"
        type="button"
        aria-label="Close navigation"
        tabIndex={open ? 0 : -1}
        onClick={close}
      />
      <aside
        className="drawer glass-raised"
        ref={drawerRef}
        role="dialog"
        aria-label="Navigation drawer"
      >
        <div className="drawer-header">
          <div className="drawer-brand">
            <span className="drawer-brand-mark">
              <CloudSun />
            </span>
            <div className="drawer-brand-info">
              <span className="drawer-title">WeatherGPT</span>
              <span className="drawer-subtitle">Atmospheric Intelligence</span>
            </div>
          </div>
          <button
            className="icon-button close-btn"
            type="button"
            aria-label="Close navigation"
            onClick={close}
          >
            <X />
          </button>
        </div>

        <div className="drawer-body">
          {currentAuth.status === 'authenticated' && (
            <div className="drawer-action-group">
              <button
                type="button"
                className="drawer-new-chat-btn"
                onClick={() => {
                  onNewChat();
                  close();
                }}
              >
                <Plus />
                <span>New Chat</span>
              </button>
              <div className="drawer-link drawer-link--disabled">
                <HistoryIcon />
                <span>Previous Chats</span>
                <small className="coming-soon-tag">Coming soon</small>
              </div>
            </div>
          )}

          <nav className="drawer-nav">
            <section className="drawer-section">
              <p className="section-eyebrow">VIEWS</p>
              <NavLink to="/" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`} end>
                <MessageSquare />
                <span>Chat Assistant</span>
              </NavLink>
              <NavLink to="/forecast" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <Sun />
                <span>Forecast</span>
              </NavLink>
              <NavLink to="/maps" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <MapIcon />
                <span>Maps</span>
              </NavLink>
              <NavLink to="/climate" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <HistoryIcon />
                <span>Climate History</span>
              </NavLink>
              <NavLink to="/voice" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <Volume2 />
                <span>Voice</span>
              </NavLink>
            </section>

            <section className="drawer-section">
              <div className="drawer-section-header">
                <p className="section-eyebrow">APPEARANCE</p>
                <span className="theme-status-tag">{theme === 'dark' ? 'Dark' : 'Light'}</span>
              </div>
              <div className="theme-segmented-control" role="group" aria-label="Theme selection">
                <button
                  type="button"
                  className={`theme-segment-btn ${theme === 'light' ? 'selected' : ''}`}
                  onClick={() => onThemeChange('light')}
                  aria-pressed={theme === 'light'}
                  aria-label="Switch to light mode"
                >
                  <Sun />
                  <span>Light</span>
                </button>
                <button
                  type="button"
                  className={`theme-segment-btn ${theme === 'dark' ? 'selected' : ''}`}
                  onClick={() => onThemeChange('dark')}
                  aria-pressed={theme === 'dark'}
                  aria-label="Switch to dark mode"
                >
                  <Moon />
                  <span>Dark</span>
                </button>
              </div>
            </section>

            <section className="drawer-section">
              <p className="section-eyebrow">APP</p>
              <NavLink to="/settings" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <Settings />
                <span>Settings</span>
              </NavLink>
              <NavLink to="/about" onClick={close} className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}>
                <Info />
                <span>About WeatherGPT</span>
              </NavLink>
            </section>
          </nav>
        </div>

        <div className="drawer-footer">
          {currentAuth.user ? (
            <div className="drawer-account-auth">
              <p className="section-eyebrow">ACCOUNT</p>
              <NavLink to="/profile" onClick={close} className="drawer-link">
                <UserRound />
                <span className="user-name-truncate">{currentAuth.user.name || currentAuth.user.email}</span>
              </NavLink>
              <button
                type="button"
                className="drawer-link logout-btn"
                onClick={() => {
                  onLogout();
                  close();
                }}
              >
                <LogOut />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="drawer-guest-box">
              <div className="guest-header">
                <span className="guest-badge-avatar">
                  <UserRound />
                </span>
                <div className="guest-meta">
                  <strong>Guest</strong>
                  <small>You’re using guest mode</small>
                </div>
              </div>
              <div className="guest-action-buttons">
                <Link to="/login" onClick={close} className="guest-btn guest-btn--login">
                  <LogIn />
                  <span>Login</span>
                </Link>
                <Link to="/signup" onClick={close} className="guest-btn guest-btn--signup">
                  <span>Sign Up</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

export function ProfileMenu({
  auth: currentAuth,
  close,
  onLogout,
}: {
  auth: AuthState;
  close: () => void;
  onLogout: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) {
        close();
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    window.addEventListener('mousedown', handleOutside);
    window.addEventListener('keydown', handleEscape);
    return () => {
      window.removeEventListener('mousedown', handleOutside);
      window.removeEventListener('keydown', handleEscape);
    };
  }, [close]);

  return (
    <div className="profile-menu glass-raised" ref={ref} role="dialog" aria-label="Profile options">
      {currentAuth.user ? (
        <div className="profile-menu-content">
          <div className="profile-card-header">
            <span className="profile-disc">
              {currentAuth.user.name ? currentAuth.user.name[0].toUpperCase() : <UserRound />}
            </span>
            <div className="profile-card-details">
              <strong>{currentAuth.user.name || 'WeatherGPT Member'}</strong>
              <small title={currentAuth.user.email}>{currentAuth.user.email}</small>
            </div>
          </div>
          <div className="profile-menu-divider" />
          <div className="profile-menu-links">
            <Link to="/profile" onClick={close} className="profile-menu-item">
              <UserRound />
              <span>Profile</span>
            </Link>
            <Link to="/settings" onClick={close} className="profile-menu-item">
              <Settings />
              <span>Settings</span>
            </Link>
            <button
              type="button"
              className="profile-menu-item logout"
              onClick={() => {
                onLogout();
                close();
              }}
            >
              <LogOut />
              <span>Logout</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="profile-menu-content">
          <div className="profile-card-header">
            <span className="profile-disc">
              <UserRound />
            </span>
            <div className="profile-card-details">
              <strong>Guest</strong>
              <small>You’re using guest mode</small>
            </div>
          </div>
          <div className="profile-menu-divider" />
          <div className="profile-guest-actions">
            <Link to="/login" onClick={close} className="profile-menu-btn profile-menu-btn--login">
              <LogIn />
              <span>Login</span>
            </Link>
            <Link to="/signup" onClick={close} className="profile-menu-btn profile-menu-btn--signup">
              <span>Sign Up</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
