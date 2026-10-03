'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';

export const TopProgressBar: React.FC = () => {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // When route finishes changing, complete the bar
    setProgress(100);
    const timeout = setTimeout(() => {
      setLoading(false);
      setProgress(0);
    }, 300);

    return () => clearTimeout(timeout);
  }, [pathname, searchParams]);

  useEffect(() => {
    // Global listener for clicking internal links
    const handleDocumentClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a');
      if (!target) return;
      const href = target.getAttribute('href');
      if (
        href &&
        href.startsWith('/') &&
        !href.startsWith('#') &&
        !target.hasAttribute('download') &&
        target.getAttribute('target') !== '_blank'
      ) {
        if (href !== pathname) {
          setLoading(true);
          setProgress(25);
          const t1 = setTimeout(() => setProgress(65), 100);
          const t2 = setTimeout(() => setProgress(85), 350);
          return () => {
            clearTimeout(t1);
            clearTimeout(t2);
          };
        }
      }
    };

    document.addEventListener('click', handleDocumentClick, { capture: true });
    return () => document.removeEventListener('click', handleDocumentClick, { capture: true });
  }, [pathname]);

  if (!loading && progress === 0) return null;

  return (
    <div
      aria-hidden="true"
      className="fixed top-0 left-0 right-0 z-50 h-[3px] bg-transparent pointer-events-none"
    >
      <div
        className="h-full bg-gradient-to-r from-[#8B5CF6] via-[#A855F7] to-[#C084FC] shadow-[0_0_12px_rgba(168,85,247,0.8)] transition-all ease-out duration-200"
        style={{
          width: `${progress}%`,
          opacity: progress === 100 ? 0 : 1,
          transitionProperty: 'width, opacity',
        }}
      />
    </div>
  );
};
