import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useEclProductData, useCohortsByProduct } from './useEclData';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
  api: {
    eclByProduct: vi.fn(),
    eclByCohort: vi.fn(),
  },
}));

const mockApi = api as unknown as {
  eclByProduct: ReturnType<typeof vi.fn>;
  eclByCohort: ReturnType<typeof vi.fn>;
};

describe('useEclProductData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not fetch when shouldFetch is false', () => {
    renderHook(() => useEclProductData(false));
    expect(mockApi.eclByProduct).not.toHaveBeenCalled();
  });

  it('fetches ECL by product when shouldFetch is true', async () => {
    const mockProducts = [
      { product_type: 'mortgage', ecl: 1000 },
      { product_type: 'auto', ecl: 500 },
    ];
    mockApi.eclByProduct.mockResolvedValue(mockProducts);
    mockApi.eclByCohort.mockResolvedValue([{ cohort: 'A', ecl: 100 }]);

    const { result } = renderHook(() => useEclProductData(true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.eclByProduct).toHaveBeenCalledOnce();
    expect(result.current.eclProduct).toEqual(mockProducts);
  });

  it('fetches cohort data for each product', async () => {
    const mockProducts = [{ product_type: 'mortgage', ecl: 1000 }];
    mockApi.eclByProduct.mockResolvedValue(mockProducts);
    mockApi.eclByCohort.mockResolvedValue([{ cohort: 'A', ecl: 100 }]);

    const { result } = renderHook(() => useEclProductData(true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.eclByCohort).toHaveBeenCalledWith('mortgage');
    expect(result.current.eclCohortByProduct).toHaveProperty('mortgage');
  });

  it('sets loading to true then false', async () => {
    mockApi.eclByProduct.mockResolvedValue([]);

    const { result } = renderHook(() => useEclProductData(true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles eclByProduct error gracefully', async () => {
    mockApi.eclByProduct.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useEclProductData(true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.eclProduct).toEqual([]);
  });

  it('handles eclByCohort error for a product gracefully', async () => {
    mockApi.eclByProduct.mockResolvedValue([{ product_type: 'mortgage', ecl: 1000 }]);
    mockApi.eclByCohort.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useEclProductData(true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.eclCohortByProduct).toEqual({});
  });
});

describe('useCohortsByProduct', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns empty object when products is empty', () => {
    const fetchFn = vi.fn();
    const { result } = renderHook(() => useCohortsByProduct([], fetchFn));
    expect(fetchFn).not.toHaveBeenCalled();
    expect(result.current).toEqual({});
  });

  it('fetches cohort data for each product', async () => {
    const fetchFn = vi.fn().mockResolvedValue([{ cohort: 'A', value: 1 }]);
    const products = [{ product_type: 'mortgage' }, { product_type: 'auto' }];

    const { result } = renderHook(() => useCohortsByProduct(products, fetchFn));

    await waitFor(() => {
      expect(Object.keys(result.current).length).toBe(2);
    });

    expect(fetchFn).toHaveBeenCalledWith('mortgage');
    expect(fetchFn).toHaveBeenCalledWith('auto');
  });

  it('uses custom productKey', async () => {
    const fetchFn = vi.fn().mockResolvedValue([{ cohort: 'A' }]);
    const products = [{ name: 'loan_a' }];

    const { result } = renderHook(() => useCohortsByProduct(products, fetchFn, 'name'));

    await waitFor(() => {
      expect(Object.keys(result.current).length).toBe(1);
    });

    expect(fetchFn).toHaveBeenCalledWith('loan_a');
  });

  it('skips products where fetch fails', async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce([{ cohort: 'A' }])
      .mockRejectedValueOnce(new Error('fail'));
    const products = [{ product_type: 'ok' }, { product_type: 'fail' }];

    const { result } = renderHook(() => useCohortsByProduct(products, fetchFn));

    await waitFor(() => {
      expect(Object.keys(result.current).length).toBe(1);
    });

    expect(result.current).toHaveProperty('ok');
    expect(result.current).not.toHaveProperty('fail');
  });

  it('skips products where fetch returns empty array', async () => {
    const fetchFn = vi.fn().mockResolvedValue([]);
    const products = [{ product_type: 'empty' }];

    const { result } = renderHook(() => useCohortsByProduct(products, fetchFn));

    await new Promise(r => setTimeout(r, 100));

    expect(result.current).toEqual({});
  });
});
