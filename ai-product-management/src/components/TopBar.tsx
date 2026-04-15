import { Bell, User, ChevronDown, Search, Monitor, Briefcase } from 'lucide-react';

interface TopBarProps {
  title?: string;
  subtitle?: string;
  viewMode?: 'pm' | 'executive';
  onToggleViewMode?: () => void;
  onOpenCommandPalette?: () => void;
  onToggleNotifications?: () => void;
  userName?: string;
}

export default function TopBar({ title, subtitle, viewMode = 'pm', onToggleViewMode, onOpenCommandPalette, onToggleNotifications, userName }: TopBarProps) {
  return (
    <header className="h-16 flex items-center justify-between px-8 border-b border-az-border bg-white/60 backdrop-blur-sm sticky top-0 z-30">
      <div>
        {title && <h1 className="text-lg font-semibold text-az-text">{title}</h1>}
        {subtitle && <p className="text-xs text-az-text-tertiary mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-2.5">
        {/* Command Palette trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-az-border bg-white text-sm text-az-text-tertiary hover:border-az-purple/20 hover:text-az-text-secondary transition-all"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="text-xs hidden md:block">Search...</span>
          <kbd className="hidden md:flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-az-surface-warm border border-az-border text-[10px] font-mono ml-2">
            ⌘K
          </kbd>
        </button>

        {/* View Mode Toggle */}
        <div className="flex items-center bg-az-surface-warm rounded-lg border border-az-border-light p-0.5">
          <button
            onClick={() => viewMode !== 'pm' && onToggleViewMode?.()}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              viewMode === 'pm'
                ? 'bg-white text-az-text shadow-sm'
                : 'text-az-text-tertiary hover:text-az-text-secondary'
            }`}
          >
            <Monitor className="w-3 h-3" />
            PM View
          </button>
          <button
            onClick={() => viewMode !== 'executive' && onToggleViewMode?.()}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              viewMode === 'executive'
                ? 'bg-white text-az-text shadow-sm'
                : 'text-az-text-tertiary hover:text-az-text-secondary'
            }`}
          >
            <Briefcase className="w-3 h-3" />
            Executive
          </button>
        </div>

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative w-9 h-9 rounded-lg flex items-center justify-center text-az-text-secondary hover:bg-az-surface-warm transition-colors"
        >
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-az-crimson rounded-full" />
        </button>

        {/* User Menu */}
        <button className="flex items-center gap-2.5 pl-3 pr-2 py-1.5 rounded-lg hover:bg-az-surface-warm transition-colors">
          <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
            <User className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-sm font-medium text-az-text leading-none">{userName || 'Lea'} M.</div>
            <div className="text-[11px] text-az-text-tertiary leading-none mt-1">Product Manager</div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-az-text-tertiary" />
        </button>
      </div>
    </header>
  );
}
