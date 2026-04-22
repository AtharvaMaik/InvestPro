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
      <span
        aria-label={`Explain ${label}`}
        className="info-button"
        role="button"
        tabIndex={0}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((value) => !value)}
        onFocus={() => setOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setOpen((value) => !value);
          }
        }}
      >
        i
      </span>
      {open ? (
        <span className="info-popover" role="tooltip">
          {description}
        </span>
      ) : null}
    </span>
  );
}
