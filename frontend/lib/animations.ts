// ========================================
// GSAP Animation Library
// ========================================

import { gsap } from "gsap";

// Page transition animations
export const pageTransitions = {
  fadeIn: (element: HTMLElement | null, duration = 0.5) => {
    if (!element) return;
    gsap.fromTo(
      element,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration, ease: "power2.out" }
    );
  },

  fadeOut: (element: HTMLElement | null, duration = 0.3) => {
    if (!element) return;
    return gsap.to(element, {
      opacity: 0,
      y: -20,
      duration,
      ease: "power2.in",
    });
  },

  slideIn: (element: HTMLElement | null, direction: "left" | "right" = "left") => {
    if (!element) return;
    const x = direction === "left" ? -50 : 50;
    gsap.fromTo(
      element,
      { opacity: 0, x },
      { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }
    );
  },
};

// Card animations
export const cardAnimations = {
  hover: (element: HTMLElement | null) => {
    if (!element) return;
    gsap.to(element, {
      scale: 1.02,
      boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)",
      duration: 0.3,
      ease: "power2.out",
    });
  },

  unhover: (element: HTMLElement | null) => {
    if (!element) return;
    gsap.to(element, {
      scale: 1,
      boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
      duration: 0.3,
      ease: "power2.out",
    });
  },

  staggerIn: (elements: HTMLElement[] | NodeListOf<HTMLElement>) => {
    gsap.fromTo(
      elements,
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.5,
        stagger: 0.1,
        ease: "power3.out",
      }
    );
  },
};

// Button animations
export const buttonAnimations = {
  click: (element: HTMLElement | null) => {
    if (!element) return;
    gsap.to(element, {
      scale: 0.95,
      duration: 0.1,
      yoyo: true,
      repeat: 1,
      ease: "power2.inOut",
    });
  },

  loading: (element: HTMLElement | null) => {
    if (!element) return;
    return gsap.to(element, {
      opacity: 0.7,
      scale: 0.98,
      duration: 0.2,
    });
  },
};

// Progress animations
export const progressAnimations = {
  updateBar: (element: HTMLElement | null, progress: number) => {
    if (!element) return;
    gsap.to(element, {
      width: `${progress}%`,
      duration: 0.5,
      ease: "power2.out",
    });
  },

  pulse: (element: HTMLElement | null) => {
    if (!element) return;
    return gsap.to(element, {
      opacity: 0.5,
      duration: 0.5,
      yoyo: true,
      repeat: -1,
      ease: "power2.inOut",
    });
  },
};

// Table animations
export const tableAnimations = {
  rowAppear: (row: HTMLElement | null, index: number) => {
    if (!row) return;
    gsap.fromTo(
      row,
      { opacity: 0, x: -20 },
      {
        opacity: 1,
        x: 0,
        duration: 0.3,
        delay: index * 0.05,
        ease: "power2.out",
      }
    );
  },

  rowsIn: (rows: HTMLElement[] | NodeListOf<HTMLElement>) => {
    gsap.fromTo(
      rows,
      { opacity: 0, y: 10 },
      {
        opacity: 1,
        y: 0,
        duration: 0.4,
        stagger: 0.03,
        ease: "power2.out",
      }
    );
  },
};

// Modal animations
export const modalAnimations = {
  open: (backdrop: HTMLElement | null, content: HTMLElement | null) => {
    if (backdrop) {
      gsap.fromTo(backdrop, { opacity: 0 }, { opacity: 1, duration: 0.2 });
    }
    if (content) {
      gsap.fromTo(
        content,
        { opacity: 0, scale: 0.9, y: 20 },
        { opacity: 1, scale: 1, y: 0, duration: 0.3, ease: "back.out(1.7)" }
      );
    }
  },

  close: (backdrop: HTMLElement | null, content: HTMLElement | null) => {
    const tl = gsap.timeline();
    if (content) {
      tl.to(content, { opacity: 0, scale: 0.9, duration: 0.2, ease: "power2.in" });
    }
    if (backdrop) {
      tl.to(backdrop, { opacity: 0, duration: 0.2 }, "-=0.1");
    }
    return tl;
  },
};

// Notification animations
export const notificationAnimations = {
  slideIn: (element: HTMLElement | null) => {
    if (!element) return;
    gsap.fromTo(
      element,
      { opacity: 0, x: 100, scale: 0.9 },
      { opacity: 1, x: 0, scale: 1, duration: 0.4, ease: "back.out(1.4)" }
    );
  },

  slideOut: (element: HTMLElement | null) => {
    if (!element) return;
    return gsap.to(element, {
      opacity: 0,
      x: 100,
      duration: 0.3,
      ease: "power2.in",
    });
  },
};

// Skeleton loading animation
export const skeletonAnimations = {
  shimmer: (element: HTMLElement | null) => {
    if (!element) return;
    return gsap.fromTo(
      element,
      { backgroundPosition: "-200% 0" },
      {
        backgroundPosition: "200% 0",
        duration: 1.5,
        repeat: -1,
        ease: "none",
      }
    );
  },
};

// Export gsap for direct use if needed
export { gsap };
