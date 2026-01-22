// ========================================
// Scroll-Triggered Animation with GSAP
// ========================================

"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { cn } from "@/lib/utils";

// Register ScrollTrigger plugin
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

interface ScrollRevealProps {
  children: React.ReactNode;
  className?: string;
  direction?: "up" | "down" | "left" | "right" | "scale" | "fade";
  delay?: number;
  duration?: number;
  distance?: number;
  once?: boolean;
}

export function ScrollReveal({
  children,
  className,
  direction = "up",
  delay = 0,
  duration = 0.8,
  distance = 40,
  once = true,
}: ScrollRevealProps) {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Define initial state based on direction
    const fromVars: gsap.TweenVars = {
      opacity: 0,
      duration,
      delay,
      ease: "power3.out",
    };

    switch (direction) {
      case "up":
        fromVars.y = distance;
        break;
      case "down":
        fromVars.y = -distance;
        break;
      case "left":
        fromVars.x = -distance;
        break;
      case "right":
        fromVars.x = distance;
        break;
      case "scale":
        fromVars.scale = 0.8;
        break;
      case "fade":
        // Just opacity
        break;
    }

    const ctx = gsap.context(() => {
      gsap.from(element, {
        ...fromVars,
        scrollTrigger: {
          trigger: element,
          start: "top 85%",
          end: "top 20%",
          toggleActions: once ? "play none none none" : "play reverse play reverse",
        },
      });
    });

    return () => ctx.revert();
  }, [direction, delay, duration, distance, once]);

  return (
    <div ref={elementRef} className={cn("opacity-0", className)}>
      {children}
    </div>
  );
}

interface CounterAnimationProps {
  value?: number;
  end?: number;
  suffix?: string;
  prefix?: string;
  className?: string;
  duration?: number;
  delay?: number;
}

export function CounterAnimation({
  value,
  end,
  suffix = "",
  prefix = "",
  className,
  duration = 2,
  delay = 0,
}: CounterAnimationProps) {
  const counterRef = useRef<HTMLSpanElement>(null);
  const displayValue = end ?? value ?? 0;

  useEffect(() => {
    const element = counterRef.current;
    if (!element || displayValue === 0) return;

    const ctx = gsap.context(() => {
      gsap.from(element, {
        textContent: 0,
        duration,
        delay,
        snap: { textContent: 1 },
        scrollTrigger: {
          trigger: element,
          start: "top 85%",
        },
        onUpdate: function () {
          const current = Math.floor(parseFloat(element.textContent || "0"));
          element.textContent = current.toLocaleString();
        },
      });
    });

    return () => ctx.revert();
  }, [displayValue, duration, delay]);

  return (
    <span className={className}>
      {prefix}
      <span ref={counterRef}>{displayValue.toLocaleString()}</span>
      {suffix}
    </span>
  );
}

export default ScrollReveal;
