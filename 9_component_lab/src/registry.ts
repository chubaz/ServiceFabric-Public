import type { ComponentType } from 'react';
import ButtonLab from './lab/ButtonLab';

export interface LabComponent {
  id: string;
  name: string;
  category: string;
  component: ComponentType;
}

export const labRegistry: LabComponent[] = [
  {
    id: 'button',
    name: 'Button',
    category: 'Basic Inputs',
    component: ButtonLab,
  },
  // Guide is hidden from dynamic category listing but registered for routes
];

export const getComponentById = (id: string) => {
  return labRegistry.find(c => c.id === id);
}

export const getGroupedComponents = () => {
  const groups: Record<string, LabComponent[]> = {};
  labRegistry.forEach(c => {
    if (!groups[c.category]) groups[c.category] = [];
    groups[c.category].push(c);
  });
  return groups;
}
