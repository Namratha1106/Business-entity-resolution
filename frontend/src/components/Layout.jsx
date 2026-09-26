import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Database, Search,
  GitCompare, Layers, Brain, BarChart,
  FileText, Upload, Maximize2, Minimize2, Palette, Check,
} from 'lucide-react'
import { useTheme } from '../theme'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Dataset', href: '/dataset', icon: Database },
  { name: 'Data Explorer', href: '/explorer', icon: Search },
  { name: 'Normalization', href: '/normalization', icon: GitCompare },
  { name: 'Blocking', href: '/blocking', icon: Layers },
  { name: 'Features', href: '/features', icon: Brain },
  { name: 'Model Training', href: '/training', icon: BarChart },
  { name: 'Evaluation', href: '/evaluation', icon: FileText },
  { name: 'Results', href: '/results', icon: Database },
  { name: 'Submission', href: '/submission', icon: Upload },
]

export default function Layout({ children }) {
  const location = useLocation()
  const { theme, setTheme, themes } = useTheme()
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const syncFullscreen = useCallback(() => {
    setIsFullscreen(Boolean(document.fullscreenElement))
  }, [])

  useEffect(() => {
    document.addEventListener('fullscreenchange', syncFullscreen)
    return () => document.removeEventListener('fullscreenchange', syncFullscreen)
  }, [syncFullscreen])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', onClickOutside)
    }
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [menuOpen])

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        setIsFullscreen(true)
        await document.documentElement.requestFullscreen()
      } else {
        setIsFullscreen(false)
        await document.exitFullscreen()
      }
    } catch (err) {
      console.error('Fullscreen toggle failed:', err)
      syncFullscreen() // Re-sync on error
    }
  }

  const currentLabel = themes.find((t) => t.id === theme)?.label || theme

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="flex">
        <aside className="theme-sidebar w-64 min-h-screen p-4 shrink-0">
          <div className="flex items-start justify-between gap-2 mb-6 px-2">
            <h1 className="sidebar-title text-xl font-bold leading-tight">
              Entity Resolution
            </h1>
            <div className="relative shrink-0" ref={menuRef} style={{ zIndex: 100 }}>
              <button
                type="button"
                onClick={() => setMenuOpen((o) => !o)}
                title="Screen & theme options"
                aria-label="Screen and theme options"
                aria-expanded={menuOpen}
                className="sidebar-btn p-2 rounded-md transition-colors"
              >
                <Palette className="w-5 h-5" />
              </button>

              {menuOpen && (
                <div style={{ position: 'fixed', right: '20px', top: '80px', zIndex: 9999, borderRadius: '8px', border: '2px solid #ffffff', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', backgroundColor: '#000000', minWidth: '350px', maxWidth: '400px', color: '#ffffff' }}>
                  <div style={{ padding: '16px', borderBottom: '2px solid #ffffff' }}>
                    <p style={{ color: '#ffff00', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>Theme</p>
                    <p style={{ color: '#ffffff', fontSize: '14px', fontWeight: 'bold', whiteSpace: 'normal', wordWrap: 'break-word' }}>{currentLabel}</p>
                  </div>
                  <ul style={{ padding: '4px 0', maxHeight: '300px', overflowY: 'auto', margin: 0, listStyle: 'none' }}>
                    {themes.map((t) => (
                      <li key={t.id} style={{ margin: 0 }}>
                        <button
                          type="button"
                          onClick={() => {
                            setTheme(t.id)
                            setMenuOpen(false)
                          }}
                          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', fontSize: '14px', textAlign: 'left', color: '#ffffff', backgroundColor: theme === t.id ? '#0000ff' : '#333333', whiteSpace: 'normal', wordWrap: 'break-word', border: '1px solid #ffffff', cursor: 'pointer' }}
                        >
                          <span style={{ flex: 1, paddingRight: '8px', wordWrap: 'break-word', color: '#ffffff', fontWeight: 'bold' }}>{t.label}</span>
                          {theme === t.id && <Check style={{ width: '16px', height: '16px', color: '#00ff00', flexShrink: 0 }} />}
                        </button>
                      </li>
                    ))}
                  </ul>
                  <div style={{ borderTop: '2px solid #ffffff', padding: '4px' }}>
                    <button
                      type="button"
                      onClick={() => {
                        toggleFullscreen()
                        setMenuOpen(false)
                      }}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', fontSize: '14px', borderRadius: '6px', color: '#ffffff', backgroundColor: '#333333', whiteSpace: 'normal', wordWrap: 'break-word', border: '1px solid #ffffff', cursor: 'pointer' }}
                    >
                      {isFullscreen ? (
                        <Minimize2 style={{ width: '16px', height: '16px', color: '#ffffff' }} />
                      ) : (
                        <Maximize2 style={{ width: '16px', height: '16px', color: '#ffffff' }} />
                      )}
                      <span style={{ color: '#ffffff', fontWeight: 'bold' }}>{isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'nav-link-active' : 'nav-link'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </aside>
        <main className="flex-1 p-8 min-w-0">
          {children}
        </main>
      </div>
    </div>
  )
}
