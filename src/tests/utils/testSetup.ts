import { jest } from '@jest/globals';

// Configure longer timeout for integration tests
jest.setTimeout(30000);

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});

// Global teardown
afterAll(async () => {
  // Close any open handles/connections
});
