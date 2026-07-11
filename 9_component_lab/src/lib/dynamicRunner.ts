import { useState, useEffect, useRef } from 'react';
import type { ExternalPackage } from './StudioRegistry';

export interface LiveScopeResult {
  scope: Record<string, any>;
  cleanCode: string;
  loading: boolean;
  error: string | null;
}

const moduleCache: Record<string, any> = {
  'react': (window as any).React,
  'react-dom': (window as any).ReactDOM,
};
(window as any).__STUDIO_MODULE_CACHE__ = moduleCache;

/**
 * Extracts import statements from a block of code and resolves them using ESM CDNs.
 */
// CDNs that support ?external=react,react-dom to prevent bundling React internally
const ESM_EXTERNAL_CDNS = ['esm.sh', 'cdn.skypack.dev'];

function buildCdnUrl(specifier: string): string {
  return `https://esm.sh/${specifier}?external=react,react-dom`;
}

function addExternalParam(url: string): string {
  if (ESM_EXTERNAL_CDNS.some(cdn => url.includes(cdn)) && !url.includes('external=')) {
    return url + (url.includes('?') ? '&' : '?') + 'external=react,react-dom';
  }
  return url;
}

export async function resolveImports(
  code: string,
  baseScope: Record<string, any>,
  packages: ExternalPackage[] = []
): Promise<{ scope: Record<string, any>, cleanCode: string }> {
  // Matches: import [specs from] 'specifier'
  // Handles: default, named {}, namespace * as X, side-effect only
  const importRegex = /import\s+(?:type\s+)?(?:([\w$*{},\s]+?)\s+from\s+)?['"]([^'"]+)['"]\s*;?/g;
  const scope: Record<string, any> = { ...baseScope };
  let cleanCode = code;
  const matches = [...code.matchAll(importRegex)];

  for (const match of matches) {
    const fullStatement = match[0];
    const importSpecs = match[1];
    const packageName = match[2];

    // Skip TypeScript type-only imports — compile-time only, no runtime value
    if (fullStatement.trimStart().startsWith('import type')) {
      cleanCode = cleanCode.replace(fullStatement, '');
      continue;
    }

    if (packageName === 'react/jsx-runtime') {
      scope['jsx'] = baseScope.React.createElement;
      scope['jsxs'] = baseScope.React.createElement;
      scope['Fragment'] = baseScope.React.Fragment;
      cleanCode = cleanCode.replace(fullStatement, '');
      continue;
    }

    // Resolve the URL to fetch from: use the registered package URL if available,
    // otherwise treat the specifier itself as the URL (or fall back to esm.sh for bare names)
    const pkg = packages.find(p => p.id === packageName || p.name === packageName);
    const resolvedUrl = pkg ? pkg.url : packageName;
    const cacheKey = resolvedUrl;

    try {
      if (!moduleCache[cacheKey]) {
        let imported: any;
        const isBareSpecifier = !resolvedUrl.startsWith('http') && !resolvedUrl.startsWith('./') && !resolvedUrl.startsWith('../');

        if (isBareSpecifier) {
          // Try browser importmap first, then fall back to esm.sh
          try {
            imported = await import(/* @vite-ignore */ resolvedUrl);
          } catch {
            imported = await import(/* @vite-ignore */ buildCdnUrl(resolvedUrl));
          }
        } else {
          // Direct URL: use as-is, but enhance known ESM CDNs with external peer-dep params
          imported = await import(/* @vite-ignore */ addExternalParam(resolvedUrl));
        }

        moduleCache[cacheKey] = imported;
      }

      const module = moduleCache[cacheKey];
      const isObject = typeof module === 'object' && module !== null;

      if (importSpecs) {
        if (importSpecs.includes('* as')) {
          const name = importSpecs.split('as')[1].trim();
          scope[name] = module;
        } else if (importSpecs.trimStart().startsWith('{')) {
          const namedImportsStr = importSpecs.replace(/[{}]/g, '');
          const namedImports = namedImportsStr.split(',').map(s => s.trim()).filter(Boolean);

          namedImports.forEach(spec => {
            // Strip leading `type` keyword from individual named imports (e.g. `{ type X }`)
            const cleanSpec = spec.replace(/^type\s+/, '');
            if (!cleanSpec) return;
            if (cleanSpec.includes(' as ')) {
              const [original, alias] = cleanSpec.split(' as ').map(s => s.trim());
              scope[alias] = module[original];
            } else {
              scope[cleanSpec] = module[cleanSpec];
            }
          });
        } else {
          const name = importSpecs.trim();
          scope[name] = isObject && 'default' in module ? module.default : module;
        }
      }

      cleanCode = cleanCode.replace(fullStatement, '');
    } catch (err: any) {
      console.warn(`Failed to resolve package: ${packageName}`, err);
      throw new Error(`Failed to resolve package "${packageName}": ${err.message}`);
    }
  }

  return { scope, cleanCode: cleanCode.trim() };
}

export function useLiveScope(code: string, baseScope: Record<string, any>, packages: ExternalPackage[] = []) {
  const [result, setResult] = useState<LiveScopeResult>({
    scope: baseScope,
    cleanCode: code,
    loading: false,
    error: null,
  });
  
  const timeoutRef = useRef<any>(null);

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    if (!code.includes('import ')) {
        setResult(prev => ({ ...prev, cleanCode: code, scope: baseScope, error: null }));
        return;
    }

    setResult(prev => ({ ...prev, loading: true }));

    timeoutRef.current = setTimeout(async () => {
      try {
        const { scope, cleanCode } = await resolveImports(code, baseScope, packages);
        setResult({
          scope,
          cleanCode,
          loading: false,
          error: null
        });
      } catch (err: any) {
        setResult(prev => ({
          ...prev,
          loading: false,
          error: err.message || 'Failed to resolve imports'
        }));
      }
    }, 500);

    return () => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [code, baseScope, JSON.stringify(packages)]);

  return result;
}
