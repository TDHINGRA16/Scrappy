// ========================================
// GSAP Animation Hook
// ========================================

"use client";

import { useRef, useEffect, useCallback } from "react";
import { gsap } from "gsap";
import {
  pageTransitions,
  cardAnimations,
  buttonAnimations,
  modalAnimations,
  tableAnimations,
} from "@/lib/animations";

// Main animation hook
export function useAnimation() {
  const ref = useRef<HTMLElement>(null);

  const fadeIn = useCallback((duration = 0.5) => {
    pageTransitions.fadeIn(ref.current, duration);
  }, []);

  const fadeOut = useCallback((duration = 0.3) => {
    return pageTransitions.fadeOut(ref.current, duration);
  }, []);

  const slideIn = useCallback((direction: "left" | "right" = "left") => {
    pageTransitions.slideIn(ref.current, direction);
  }, []);

  return { ref, fadeIn, fadeOut, slideIn };
}

// Page transition hook - auto-animates on mount
export function usePageTransition(options: { delay?: number } = {}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      gsap.set(ref.current, { opacity: 0, y: 20 });
      gsap.to(ref.current, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        delay: options.delay || 0,
        ease: "power2.out",
      });
    }
  }, [options.delay]);

  return ref;
}

// Card hover animation hook
export function useCardHover() {
  const ref = useRef<HTMLDivElement>(null);

  const onMouseEnter = useCallback(() => {
    cardAnimations.hover(ref.current);
  }, []);

  const onMouseLeave = useCallback(() => {
    cardAnimations.unhover(ref.current);
  }, []);

  return { ref, onMouseEnter, onMouseLeave };
}

// Button click animation hook
export function useButtonAnimation() {
  const ref = useRef<HTMLButtonElement>(null);

  const animate = useCallback(() => {
    buttonAnimations.click(ref.current);
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    if (loading) {
      buttonAnimations.loading(ref.current);
    } else if (ref.current) {
      gsap.to(ref.current, { opacity: 1, scale: 1, duration: 0.2 });
    }
  }, []);

  return { ref, animate, setLoading };
}

// Stagger animation hook for lists
export function useStaggerAnimation<T extends HTMLElement>() {
  const containerRef = useRef<T>(null);

  const animateChildren = useCallback((selector = "> *") => {
    if (containerRef.current) {
      const elements = containerRef.current.querySelectorAll(selector);
      cardAnimations.staggerIn(elements as NodeListOf<HTMLElement>);
    }
  }, []);

  return { containerRef, animateChildren };
}

// Modal animation hook
export function useModalAnimation() {
  const backdropRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const open = useCallback(() => {
    modalAnimations.open(backdropRef.current, contentRef.current);
  }, []);

  const close = useCallback(() => {
    return modalAnimations.close(backdropRef.current, contentRef.current);
  }, []);

  return { backdropRef, contentRef, open, close };
}

// Table row animation hook
export function useTableAnimation() {
  const tableRef = useRef<HTMLTableElement>(null);

  const animateRows = useCallback(() => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll("tbody tr");
      tableAnimations.rowsIn(rows as NodeListOf<HTMLElement>);
    }
  }, []);

  return { tableRef, animateRows };
}

// Counter animation hook
export function useCounterAnimation(
  targetValue: number,
  duration = 1.5
) {
  const ref = useRef<HTMLSpanElement>(null);
  const valueRef = useRef({ value: 0 });

  useEffect(() => {
    if (ref.current) {
      gsap.to(valueRef.current, {
        value: targetValue,
        duration,
        ease: "power2.out",
        onUpdate: () => {
          if (ref.current) {
            ref.current.textContent = Math.round(valueRef.current.value).toString();
          }
        },
      });
    }
  }, [targetValue, duration]);

  return ref;
}

export default useAnimation;
