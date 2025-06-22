// Vitest Setup File
// You can use this file to set up global configurations or mocks for your tests.

import { beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';

// Ensure a fresh Pinia instance is active for every test
beforeEach(() => {
  setActivePinia(createPinia());
});

// Optional: Mock global browser objects if not fully supported by happy-dom/jsdom
// For example, localStorage mock (happy-dom usually provides a good enough one)
// const localStorageMock = (() => {
//   let store: Record<string, string> = {};
//   return {
//     getItem: (key: string) => store[key] || null,
//     setItem: (key: string, value: string) => (store[key] = value.toString()),
//     removeItem: (key: string) => delete store[key],
//     clear: () => (store = {}),
//   };
// })();
// vi.stubGlobal('localStorage', localStorageMock);


// Optional: Mock global 'fetch' or other browser APIs if your tests need them
// and they are not part of your testing environment.
// global.fetch = vi.fn(() => Promise.resolve({ json: () => Promise.resolve({}) }));


// Clean up mocks after each test if using vi.spyOn or vi.fn within tests directly
// afterEach(() => {
//   vi.restoreAllMocks(); // or vi.clearAllMocks();
// });

console.log('Vitest global setup file loaded.');
```
