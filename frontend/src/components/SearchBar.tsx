"use client";

import { useEffect, useRef, useState } from "react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  totalJobs: number;
}

export default function SearchBar({ value, onChange, totalJobs }: SearchBarProps) {
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && !focused) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focused]);

  return (
    <div className="relative w-full">
      <div
        className={`relative flex items-center rounded-xl border bg-card transition-all duration-200 ${
          focused
            ? "border-accent shadow-[0_0_0_3px_rgba(37,99,235,0.1)]"
            : "border-border hover:border-zinc-300"
        }`}
      >
        <svg
          className="absolute left-4 h-4 w-4 text-muted-foreground"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={`Search ${totalJobs > 0 ? totalJobs.toLocaleString() : ""} remote jobs...`}
          className="w-full rounded-xl bg-transparent py-3 pl-11 pr-12 text-sm text-foreground outline-none placeholder:text-muted-foreground"
        />
        {!value && !focused && (
          <kbd className="absolute right-3 hidden rounded-md border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline-block">
            /
          </kbd>
        )}
        {value && (
          <button
            onClick={() => onChange("")}
            className="absolute right-3 rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6L6 18" />
              <path d="M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
