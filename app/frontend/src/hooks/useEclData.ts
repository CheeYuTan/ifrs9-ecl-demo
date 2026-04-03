import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

/**
 * Fetches ECL by product and the per-product cohort breakdown.
 * Reusable across ModelExecution, StressTesting, Overlays, SignOff.
 */
export function useEclProductData(shouldFetch: boolean) {
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [eclCohortByProduct, setEclCohortByProduct] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!shouldFetch) return;
    setLoading(true);
    api.eclByProduct()
      .then(async (ep) => {
        setEclProduct(ep);
        const cohortMap: Record<string, any[]> = {};
        for (const row of ep) {
          try {
            cohortMap[row.product_type] = await api.eclByCohort(row.product_type);
          } catch { /* skip */ }
        }
        setEclCohortByProduct(cohortMap);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [shouldFetch]);

  return { eclProduct, eclCohortByProduct, loading };
}

/**
 * Fetches cohort data for a list of products using a given fetcher.
 * Reusable for portfolio cohorts (DataProcessing) or ECL cohorts.
 */
export function useCohortsByProduct(
  products: any[],
  fetchFn: (product: string) => Promise<any[]>,
  productKey = 'product_type',
) {
  const [cohortByProduct, setCohortByProduct] = useState<Record<string, any[]>>({});

  const load = useCallback(async () => {
    if (!products.length) return;
    const map: Record<string, any[]> = {};
    await Promise.all(
      products.map(async (row) => {
        try {
          const data = await fetchFn(row[productKey]);
          if (data?.length) map[row[productKey]] = data;
        } catch { /* skip */ }
      }),
    );
    setCohortByProduct({ ...map });
  }, [products, fetchFn, productKey]);

  useEffect(() => { load(); }, [load]);

  return cohortByProduct;
}
