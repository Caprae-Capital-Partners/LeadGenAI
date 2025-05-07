// lib/utils.ts

/**
 * Combines class names conditionally.
 * Example: cn("btn", isActive && "btn-active") → "btn btn-active"
 */
// lib/utils.ts

type ClassValue = string | number | null | boolean | undefined | Record<string, boolean>;

export function cn(...inputs: ClassValue[]): string {
  return inputs
    .flatMap((input) => {
      if (!input) return [];

      if (typeof input === "string" || typeof input === "number") {
        return [input];
      }

      if (typeof input === "object") {
        return Object.entries(input)
          .filter(([_, value]) => Boolean(value))
          .map(([key]) => key);
      }

      return [];
    })
    .join(" ");
}


/**
 * Capitalizes the first letter of a word.
 * Example: capitalize("hello") → "Hello"
 */
export function capitalize(word: string): string {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

/**
 * Formats a date string into a human-readable format.
 * Example: formatDate("2024-10-01") → "10/1/2024"
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString();
}

/**
 * Debounce function to limit how often a function is called.
 * Usage:
 * const debouncedFn = debounce(() => doSomething(), 300);
 */
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
