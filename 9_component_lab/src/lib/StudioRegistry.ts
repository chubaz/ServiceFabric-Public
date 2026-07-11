export interface DynamicComponent {
  id: string;
  name: string;
  category: 'Basic Inputs' | 'Complex Components';
  code: string;
  updatedAt: number;
}

export interface ExternalPackage {
  id: string;
  name: string;
  url: string;
}

const STORAGE_KEY = 'fabric_studio_components';
const PACKAGE_STORAGE_KEY = 'fabric_studio_packages';

export const getStoredComponents = (): DynamicComponent[] => {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored ? JSON.parse(stored) : [];
};

export const saveComponent = (comp: Omit<DynamicComponent, 'updatedAt'>) => {
  const components = getStoredComponents();
  const index = components.findIndex(c => c.id === comp.id);
  
  const newComp: DynamicComponent = {
    ...comp,
    updatedAt: Date.now()
  };

  if (index >= 0) {
    components[index] = newComp;
  } else {
    components.push(newComp);
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(components));
  window.dispatchEvent(new CustomEvent('fabric_studio_update'));
};

export const renameComponent = (oldId: string, newName: string) => {
  const components = getStoredComponents();
  const index = components.findIndex(c => c.id === oldId);
  if (index === -1) return oldId;

  const newId = newName.toLowerCase().replace(/\s+/g, '-');
  
  let finalId = newId;
  let counter = 1;
  while (components.find(c => c.id === finalId && c.id !== oldId)) {
    finalId = `${newId}-${counter}`;
    counter++;
  }

  components[index] = {
    ...components[index],
    id: finalId,
    name: newName,
    updatedAt: Date.now()
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(components));
  window.dispatchEvent(new CustomEvent('fabric_studio_update'));
  return finalId;
};

export const deleteComponent = (id: string) => {
  const components = getStoredComponents().filter(c => c.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(components));
  window.dispatchEvent(new CustomEvent('fabric_studio_update'));
};

export const getStoredPackages = (): ExternalPackage[] => {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(PACKAGE_STORAGE_KEY);
  return stored ? JSON.parse(stored) : [
    { id: 'framer-motion', name: 'Framer Motion', url: 'framer-motion' },
    { id: 'canvas-confetti', name: 'Confetti', url: 'canvas-confetti' },
    { id: 'lucide-react', name: 'Lucide Icons', url: 'lucide-react' }
  ];
};

export const savePackage = (pkg: ExternalPackage) => {
  const packages = getStoredPackages();
  const index = packages.findIndex(p => p.id === pkg.id);
  if (index >= 0) {
    packages[index] = pkg;
  } else {
    packages.push(pkg);
  }
  localStorage.setItem(PACKAGE_STORAGE_KEY, JSON.stringify(packages));
  window.dispatchEvent(new CustomEvent('fabric_studio_packages_update'));
};

export const deletePackage = (id: string) => {
  const packages = getStoredPackages().filter(p => p.id !== id);
  localStorage.setItem(PACKAGE_STORAGE_KEY, JSON.stringify(packages));
  window.dispatchEvent(new CustomEvent('fabric_studio_packages_update'));
};
