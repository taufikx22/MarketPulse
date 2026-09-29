const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Brand {
  id: number;
  name: string;
  url: string;
  category: string;
  created_at: string;
}

export interface Product {
  id: number;
  brand_id: number;
  name: string;
  url: string;
  price: number | null;
  description: string | null;
  image_url: string | null;
  last_scraped_at: string | null;
}

export interface Review {
  id: number;
  product_id: number;
  raw_text: string;
  cleaned_text: string | null;
  rating: number | null;
  author: string | null;
  review_date: string | null;
  scraped_at: string;
}

export interface SentimentTrend {
  week: string;
  sentiment: string;
  count: number;
  avg_score: number;
}

export interface ThemeData {
  theme: string;
  count: number;
  avg_score: number;
}

export interface Insight {
  id: number;
  brand_id: number;
  product_id?: number | null;
  type: string;
  text: string;
  generated_at: string;
  supporting_review_ids: number[] | null;
  supporting_reviews?: Review[];
  severity?: 'critical' | 'high' | 'medium' | 'low';
  status?: string;
  metric?: string | null;
  baseline_value?: number | null;
  current_value?: number | null;
  deviation?: number | null;
  threshold?: number | null;
}

export interface ComparisonData {
  brand_id: number;
  brand_name: string;
  product_count: number;
  avg_price: number;
  review_count: number;
  avg_rating: number;
  sentiment: Record<string, number>;
  top_themes: { theme: string; count: number }[];
}

export interface SearchResult {
  review_id: number;
  text: string;
  sentiment: string;
  distance: number | null;
  relevance?: number | null;
  product_name?: string;
  author?: string;
  date?: string;
  rating?: number;
}

export const api = {
  brands: () => fetcher<Brand[]>('/brands'),
  brand: (id: number) => fetcher<Brand>(`/brands/${id}`),
  products: (brandId: number) => fetcher<Product[]>(`/brands/${brandId}/products`),
  reviews: (brandId: number, limit = 50) => fetcher<Review[]>(`/brands/${brandId}/reviews?limit=${limit}`),
  sentimentTrend: (brandId: number) => fetcher<SentimentTrend[]>(`/brands/${brandId}/sentiment-trend`),
  themes: (brandId: number) => fetcher<ThemeData[]>(`/brands/${brandId}/themes`),
  insights: (brandIdOrOptions?: number | { brandId?: number; severity?: string; status?: string; isAnomaly?: boolean }) => {
    if (typeof brandIdOrOptions === 'number') {
      return fetcher<Insight[]>(`/insights?brand_id=${brandIdOrOptions}`);
    }
    const params = new URLSearchParams();
    if (brandIdOrOptions?.brandId) params.append('brand_id', String(brandIdOrOptions.brandId));
    if (brandIdOrOptions?.severity) params.append('severity', brandIdOrOptions.severity);
    if (brandIdOrOptions?.status) params.append('status', brandIdOrOptions.status);
    if (brandIdOrOptions?.isAnomaly !== undefined) params.append('is_anomaly', String(brandIdOrOptions.isAnomaly));
    const qs = params.toString();
    return fetcher<Insight[]>(qs ? `/insights?${qs}` : '/insights');
  },
  detectAnomalies: (brandId?: number) => {
    const url = brandId ? `/insights/detect-anomalies?brand_id=${brandId}` : '/insights/detect-anomalies';
    return fetcher<{ status: string; anomalies_detected: number; anomalies: Record<string, unknown>[] }>(url, { method: 'POST' });
  },
  compare: (ids: number[]) => fetcher<ComparisonData[]>(`/compare?brand_ids=${ids.join(',')}`),
  search: (query: string, brandId?: number, sentiment?: string, n = 15) => {
    let url = `/search?q=${encodeURIComponent(query)}&n=${n}`;
    if (brandId) url += `&brand_id=${brandId}`;
    if (sentiment) url += `&sentiment=${sentiment}`;
    return fetcher<{ query: string; results: SearchResult[] }>(url);
  },
};

