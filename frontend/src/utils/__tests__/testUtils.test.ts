// Simple utility function tests to demonstrate the testing framework

describe('Test Framework Validation', () => {
  test('basic math operations work', () => {
    expect(2 + 2).toBe(4);
    expect(3 * 3).toBe(9);
    expect(10 / 2).toBe(5);
  });

  test('string operations work', () => {
    expect('hello'.toUpperCase()).toBe('HELLO');
    expect('world'.length).toBe(5);
    expect('test'.includes('es')).toBe(true);
  });

  test('array operations work', () => {
    const arr = [1, 2, 3, 4, 5];
    expect(arr.length).toBe(5);
    expect(arr.includes(3)).toBe(true);
    expect(arr.filter(x => x > 3)).toEqual([4, 5]);
  });

  test('object operations work', () => {
    const obj = { name: 'test', value: 42 };
    expect(obj.name).toBe('test');
    expect(obj.value).toBe(42);
    expect(Object.keys(obj)).toEqual(['name', 'value']);
  });

  test('promises work', async () => {
    const promise = Promise.resolve('success');
    await expect(promise).resolves.toBe('success');
  });

  test('async/await works', async () => {
    const asyncFunction = async () => {
      await new Promise(resolve => setTimeout(resolve, 1));
      return 'async result';
    };

    const result = await asyncFunction();
    expect(result).toBe('async result');
  });
});

// Mock function tests
describe('Mock Function Tests', () => {
  test('jest.fn() works correctly', () => {
    const mockFn = jest.fn();
    
    mockFn('arg1', 'arg2');
    mockFn('arg3');
    
    expect(mockFn).toHaveBeenCalledTimes(2);
    expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
    expect(mockFn).toHaveBeenLastCalledWith('arg3');
  });

  test('mock return values work', () => {
    const mockFn = jest.fn();
    mockFn.mockReturnValue('mocked value');
    
    expect(mockFn()).toBe('mocked value');
  });

  test('mock implementation works', () => {
    const mockFn = jest.fn();
    mockFn.mockImplementation((x: number) => x * 2);
    
    expect(mockFn(5)).toBe(10);
    expect(mockFn(3)).toBe(6);
  });
});

// Date and time tests
describe('Date and Time Tests', () => {
  test('date operations work', () => {
    const now = new Date();
    expect(now).toBeInstanceOf(Date);
    expect(typeof now.getTime()).toBe('number');
  });

  test('date mocking works', () => {
    const mockDate = new Date('2023-01-01T00:00:00.000Z');
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
    
    expect(new Date()).toBe(mockDate);
    
    jest.restoreAllMocks();
  });
});

// Error handling tests
describe('Error Handling Tests', () => {
  test('error throwing works', () => {
    const throwError = () => {
      throw new Error('Test error');
    };
    
    expect(throwError).toThrow('Test error');
    expect(throwError).toThrow(Error);
  });

  test('async error handling works', async () => {
    const asyncThrow = async () => {
      throw new Error('Async error');
    };
    
    await expect(asyncThrow()).rejects.toThrow('Async error');
  });
});