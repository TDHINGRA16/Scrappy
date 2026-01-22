// ========================================
// Page Transition Animation with GSAP
// ========================================

"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { usePathname } from "next/navigation";

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    // Skip animation on initial render
    if (!contentRef.current) return;

    const ctx = gsap.context(() => {
      // Animate content in
      gsap.fromTo(
        contentRef.current,
        {
          opacity: 0,
          y: 20,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.6,
          ease: "power3.out",
        }
      );
    });

    return () => ctx.revert();
  }, [pathname]);

  return (
    <div ref={contentRef} className="w-full">
      {children}
    </div>
  );
}

export default PageTransition;
