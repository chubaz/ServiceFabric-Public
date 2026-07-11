import { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Box, BookOpen, Layers, Sparkles, Trash2 } from 'lucide-react';
import { getGroupedComponents } from '../../registry';
import { getStoredComponents, deleteComponent } from '../../lib/StudioRegistry';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const grouped = getGroupedComponents();
  const [dynamicComponents, setDynamicComponents] = useState(getStoredComponents());

  useEffect(() => {
    const handleUpdate = () => {
      setDynamicComponents(getStoredComponents());
    };

    window.addEventListener('fabric_studio_update', handleUpdate);
    return () => window.removeEventListener('fabric_studio_update', handleUpdate);
  }, []);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (confirm('Are you sure you want to delete this component?')) {
      deleteComponent(id);
      if (location.pathname === `/lab/${id}`) {
        navigate('/');
      }
    }
  };

  return (
    <div className="w-72 border-r border-white/5 bg-[#0A0A0B] h-screen flex flex-col shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-white/5 gap-3 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Box className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col">
            <span className="font-bold text-white tracking-tight leading-none text-sm">Component Lab</span>
            <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-widest mt-1">v1.0 Studio</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
        <div>
          <h4 className="px-3 text-[11px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-3">Navigation</h4>
          <div className="space-y-1">
            <NavLink 
              to="/" 
              className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Studio Overview
            </NavLink>
            <NavLink 
              to="/studio" 
              className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
            >
              <Sparkles className="w-4 h-4" />
              Component Studio
            </NavLink>
            <NavLink 
              to="/docs" 
              className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
            >
              <BookOpen className="w-4 h-4" />
              Creator Guide
            </NavLink>
          </div>
        </div>
        
        {['Basic Inputs', 'Complex Components'].map(category => {
          const staticItems = (grouped[category] || []);
          const dynamicItems = dynamicComponents.filter(c => c.category === category);
          
          if (staticItems.length === 0 && dynamicItems.length === 0) return null;

          return (
            <div key={category}>
              <h4 className="px-3 text-[11px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-3">
                {category}
              </h4>
              <div className="space-y-1">
                {/* Static Items */}
                {staticItems.map(item => (
                  <NavLink
                    key={item.id}
                    to={`/component/${item.id}`}
                    className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
                  >
                    {({ isActive }) => (
                      <>
                        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]' : 'bg-zinc-700'}`} />
                        {item.name}
                      </>
                    )}
                  </NavLink>
                ))}

                {/* Dynamic Items */}
                {dynamicItems.map(item => (
                  <NavLink
                    key={item.id}
                    to={`/lab/${item.id}`}
                    className={({isActive}) => `group/item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
                  >
                    {({ isActive }) => (
                      <>
                        <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]' : 'bg-zinc-700'}`} />
                        {item.name}
                        <span className="ml-auto text-[8px] font-black bg-white/5 px-1.5 py-0.5 rounded text-zinc-600 uppercase tracking-tighter group-hover/item:hidden">Lab</span>
                        <button
                          onClick={(e) => handleDelete(e, item.id)}
                          className="hidden group-hover/item:flex ml-auto p-1 rounded hover:bg-red-500/20 text-zinc-500 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}

        {/* Catch-all for any other categories */}
        {Object.entries(grouped)
          .filter(([cat]) => !['Basic Inputs', 'Complex Components'].includes(cat))
          .map(([category, items]) => (
            <div key={category}>
               <h4 className="px-3 text-[11px] font-bold text-zinc-500 uppercase tracking-[0.2em] mb-3">{category}</h4>
               <div className="space-y-1">
                  {items.map(item => (
                    <NavLink
                      key={item.id}
                      to={`/component/${item.id}`}
                      className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'}`}
                    >
                      {({ isActive }) => (
                        <>
                          <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]' : 'bg-zinc-700'}`} />
                          {item.name}
                        </>
                      )}
                    </NavLink>
                  ))}
               </div>
            </div>
          ))}
      </div>

      <div className="p-4 mt-auto border-t border-white/5 bg-zinc-900/30">
        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
             <Layers className="w-4 h-4 text-indigo-400" />
             <span className="text-xs text-indigo-200 font-medium">Ready for deployment</span>
        </div>
      </div>
    </div>
  );
}
