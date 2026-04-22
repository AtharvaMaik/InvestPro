"use client";

import { useState } from "react";

type Props = {
  label: string;
  description: string;
};

export function InfoButton({ label, description }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <span className="info-wrap" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button
        aria-label={`Explain ${label}`}
        className="info-button"
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((value) => !value)}
        onFocus={() => setOpen(true)}
        type="button"
      >
        i
      </button>
      {open ? (
        <span className="info-popover" role="tooltip">
          {description}
        </span>
      ) : null}
    </span>
  );
}
