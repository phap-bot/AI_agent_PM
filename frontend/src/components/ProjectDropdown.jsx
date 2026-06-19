import { useState, useRef, useEffect } from 'react';

export default function ProjectDropdown({ 
  projects, 
  activeProjectId, 
  onChange, 
  onCreateNew, 
  onEdit, 
  onDelete 
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeProject = projects.find(p => p.id === activeProjectId);

  return (
    <div className="relative flex items-center gap-2" ref={dropdownRef}>
      <span className="text-sm font-medium text-on-surface-variant"></span>
      
      <div className="flex items-center bg-surface border border-outline-variant rounded-lg hover:border-primary/50 transition-colors shadow-sm">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-between min-w-[200px] px-3 py-2 text-sm font-medium focus:outline-none"
        >
          <span className="truncate max-w-[160px]">
            {activeProject ? activeProject.name : '-- Chọn dự án --'}
          </span>
          <span className={`material-symbols-outlined text-[18px] text-outline transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
            expand_more
          </span>
        </button>

        {activeProjectId && (
          <div className="flex items-center pr-1 border-l border-outline-variant/30 pl-1 h-full">
            <button 
              onClick={(e) => { e.stopPropagation(); onEdit(); setIsOpen(false); }}
              className="p-1.5 text-on-surface-variant hover:text-primary transition-colors hover:bg-primary/10 rounded-md"
              title="Đổi tên dự án"
            >
              <span className="material-symbols-outlined text-[16px]">edit</span>
            </button>
            <button 
              onClick={(e) => { e.stopPropagation(); onDelete(); setIsOpen(false); }}
              className="p-1.5 text-on-surface-variant hover:text-error transition-colors hover:bg-error/10 rounded-md"
              title="Xóa dự án"
            >
              <span className="material-symbols-outlined text-[16px]">delete</span>
            </button>
          </div>
        )}
      </div>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-[280px] bg-surface rounded-xl shadow-lg border border-outline-variant overflow-hidden z-[100] animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="max-h-[300px] overflow-y-auto sidebar-scroll py-1">
            {projects.map(p => (
              <button
                key={p.id}
                onClick={() => {
                  onChange(p.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between group ${
                  activeProjectId === p.id 
                    ? 'bg-primary/10 text-primary font-bold' 
                    : 'text-on-surface hover:bg-surface-container-highest'
                }`}
              >
                <span className="truncate pr-4">{p.name}</span>
                {activeProjectId === p.id && (
                  <span className="material-symbols-outlined text-[18px]">check</span>
                )}
              </button>
            ))}
            
            {projects.length === 0 && (
              <div className="px-4 py-3 text-sm text-outline text-center">
                Chưa có dự án nào
              </div>
            )}
          </div>
          
          <div className="border-t border-outline-variant/30 p-1">
            <button
              onClick={() => {
                onCreateNew();
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm font-bold text-primary hover:bg-primary/10 transition-colors rounded-lg flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
              Tạo dự án mới
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
