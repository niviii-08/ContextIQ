import "@testing-library/jest-dom/vitest";

// jsdom does not implement ResizeObserver, which Recharts' ResponsiveContainer
// relies on. Provide a minimal stub so chart-bearing components can render
// in tests without crashing.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (typeof global.ResizeObserver === "undefined") {
  (global as unknown as { ResizeObserver: unknown }).ResizeObserver =
    ResizeObserverStub;
}
