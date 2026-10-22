import { Link } from 'react-router-dom'
import type { Theme } from '../hooks/useTheme'

interface Props {
  theme: Theme
  onToggleTheme: () => void
}

export function Header({ theme, onToggleTheme }: Props) {
  return (
    <header className="app-header">
      <Link to="/" className="brand">
        <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
          <path d="M4 15 16 5l12 10v13H4z" fill="currentColor" />
          <path d="M13 28v-8h6v8" fill="var(--c-surface)" />
        </svg>
        <span>Hypotekárna kalkulačka</span>
      </Link>
      <button
        type="button"
        className="btn ghost theme-toggle"
        onClick={onToggleTheme}
        aria-label={theme === 'dark' ? 'Prepnúť na svetlú tému' : 'Prepnúť na tmavú tému'}
      >
        {theme === 'dark' ? '☀︎ Svetlá' : '☾ Tmavá'}
      </button>
    </header>
  )
}
