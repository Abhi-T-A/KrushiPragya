/**
 * Market API Client: Connects to KrushiPragya Mandi Price Discovery & Farmer Marketplace.
 */
import { api } from './api';

export interface MarketCrop {
  id: string;
  code: string;
  name_en: string;
  name_kn: string;
  official_mappings?: Array<{ commodity: string; variety: string }>;
}

export interface LatestMandiPrice {
  min: string;
  max: string;
  modal: string;
  unit: string;
  date: string;
  arrival_quantity?: string;
  is_seeded?: boolean;
  data_mode?: string;
}

export interface NearbyMandiItem {
  market_id: string;
  name: string;
  district: string;
  state: string;
  distance_km: number;
  latest_price: LatestMandiPrice | null;
  trend: 'UP' | 'DOWN' | 'STABLE';
  is_followed: boolean;
}

export interface NearbyMandisResponse {
  crop_id: string;
  crop_name: string;
  crop_code: string;
  reference_latitude: number;
  reference_longitude: number;
  radius_km: number;
  total_mandis: number;
  mandis: NearbyMandiItem[];
}

export interface DailyPriceRecord {
  date: string;
  min_price: string;
  max_price: string;
  modal_price: string;
  arrival_quantity?: string;
  variety?: string;
  unit: string;
  is_seeded?: boolean;
  data_mode?: string;
}

export interface MandiDetailResponse {
  market: {
    id: string;
    code: string;
    name: string;
    state: string;
    district: string;
    taluk?: string;
    latitude: number;
    longitude: number;
    is_active: boolean;
  };
  crop_id?: string;
  crop_name?: string;
  is_followed: boolean;
  intelligence?: {
    market_id: string;
    crop_id: string;
    crop_name: string;
    market_name: string;
    district: string;
    state: string;
    latest_price: string;
    price_change_amount: string;
    price_change_pct: string;
    trend_15d: 'UP' | 'DOWN' | 'STABLE';
    period_min_price: string;
    period_max_price: string;
    period_avg_price: string;
    history: DailyPriceRecord[];
    is_seeded?: boolean;
    data_mode?: string;
    source_name?: string;
  } | null;
}

export interface ProduceListingItem {
  listing: {
    id: string;
    farmer_id: string;
    crop_id: string;
    quantity: string | number;
    unit: string;
    quality_grade: string;
    expected_price: string | number;
    location: string;
    status: string;
    created_at: string;
    updated_at: string;
  };
  crop_name: string;
  farmer_name?: string;
  reference_mandi?: {
    mandi_name: string;
    mandi_id: string;
    district: string;
    state: string;
    distance_km?: number;
    min_price: string;
    modal_price: string;
    max_price: string;
    price_date: string;
    unit: string;
    is_seeded?: boolean;
    data_mode?: string;
  } | null;
  offers_count: number;
}

export interface BuyerOfferItem {
  offer: {
    id: string;
    listing_id: string;
    buyer_id: string;
    offered_price: string | number;
    quantity: string | number;
    message?: string;
    status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'NEGOTIATING' | 'COMPLETED';
    created_at: string;
    updated_at: string;
  };
  listing: ProduceListingItem['listing'];
  buyer_name?: string;
  farmer_expected_price: string | number;
  reference_mandi?: ProduceListingItem['reference_mandi'];
  contact_phone?: string | null;
  contact_name?: string | null;
  contact_role?: 'BUYER' | 'FARMER' | null;
}

export interface PaymentOrderResponse {
  transaction_id: string;
  offer_id: string;
  listing_id: string;
  amount: string | number;
  currency: string;
  provider?: string;
  gateway_order_id?: string | null;
  gateway_key_id?: string | null;
  gateway_configured: boolean;
  payment_status: string;
  order_status: string;
  checkout_data?: {
    action_url: string;
    params: Record<string, string>;
  } | null;
  message_kn: string;
  message_en: string;
}

export interface TransactionDetail {
  id: string;
  offer_id: string;
  listing_id: string;
  crop_name?: string;
  quantity?: string | number;
  unit?: string;
  unit_price?: string | number;
  buyer_id: string;
  buyer_name?: string;
  buyer_phone?: string;
  farmer_id: string;
  farmer_name?: string;
  farmer_phone?: string;
  amount: string | number;
  currency: string;
  gateway_order_id?: string | null;
  gateway_payment_id?: string | null;
  payment_status: string;
  order_status: string;
  failure_reason?: string | null;
  created_at: string;
  updated_at: string;
}

// ==============================================================================
// 1. Mandi Price Discovery Endpoints
// ==============================================================================

export const fetchMarketCrops = async (): Promise<MarketCrop[]> => {
  const res = await api.get<MarketCrop[]>('/market/crops');
  return res.data;
};

export const fetchNearbyMandis = async (params: {
  crop_id: string;
  latitude?: number;
  longitude?: number;
  radius_km?: number;
  sort?: 'distance' | 'price';
}): Promise<NearbyMandisResponse> => {
  const query = new URLSearchParams();
  query.append('crop_id', params.crop_id);
  if (params.latitude !== undefined) query.append('latitude', String(params.latitude));
  if (params.longitude !== undefined) query.append('longitude', String(params.longitude));
  if (params.radius_km !== undefined) query.append('radius_km', String(params.radius_km));
  if (params.sort) query.append('sort', params.sort);

  const requestUrl = `/market/mandis/nearby?${query.toString()}`;
  console.log('[MARKET] nearby API URL:', requestUrl);

  const res = await api.get<any>(requestUrl);
  console.log('[MARKET] response status:', res.status);

  const raw = res.data;
  const mandisList: NearbyMandiItem[] = raw.mandis || raw.markets || [];
  const totalCount = raw.total_mandis ?? raw.count ?? mandisList.length;

  console.log('[MARKET] total mandis:', totalCount);
  console.log('[MARKET] returned mandis:', mandisList.length);

  return {
    crop_id: raw.crop_id,
    crop_name: raw.crop_name || raw.crop || '',
    crop_code: raw.crop_code || '',
    reference_latitude: raw.reference_latitude ?? params.latitude ?? 0,
    reference_longitude: raw.reference_longitude ?? params.longitude ?? 0,
    radius_km: raw.radius_km ?? params.radius_km ?? 500,
    total_mandis: totalCount,
    mandis: mandisList,
  };
};

export const fetchMandiDetail = async (mandi_id: string, crop_id?: string): Promise<MandiDetailResponse> => {
  const url = crop_id ? `/market/mandis/${mandi_id}?crop_id=${crop_id}` : `/market/mandis/${mandi_id}`;
  const res = await api.get<any>(url);
  const data = res.data;
  if (data?.intelligence) {
    const rawIntel = data.intelligence;
    data.intelligence = {
      ...rawIntel,
      latest_price: rawIntel.current ? String(rawIntel.current) : rawIntel.latest_price,
      price_change_pct: rawIntel.change_percent !== undefined ? String(rawIntel.change_percent) : rawIntel.price_change_pct,
      trend_15d: rawIntel.trend || rawIntel.trend_15d || 'STABLE',
      period_min_price: rawIntel.lowest_15_days !== undefined ? String(rawIntel.lowest_15_days) : rawIntel.period_min_price,
      period_max_price: rawIntel.highest_15_days !== undefined ? String(rawIntel.highest_15_days) : rawIntel.period_max_price,
    };
  }
  return data;
};

export const followMandi = async (mandi_id: string, farmer_id: string): Promise<void> => {
  await api.post(`/market/mandis/${mandi_id}/follow`, {}, { headers: { 'x-farmer-id': farmer_id } });
};

export const unfollowMandi = async (mandi_id: string, farmer_id: string): Promise<void> => {
  await api.delete(`/market/mandis/${mandi_id}/follow`, { headers: { 'x-farmer-id': farmer_id } });
};

// ==============================================================================
// 2. Farmer Produce Listings Endpoints
// ==============================================================================

export const fetchProduceListings = async (params?: {
  crop_id?: string;
  quality_grade?: string;
  max_price?: number;
  min_quantity?: number;
  status?: string;
}): Promise<ProduceListingItem[]> => {
  const query = new URLSearchParams();
  if (params?.crop_id) query.append('crop_id', params.crop_id);
  if (params?.quality_grade) query.append('quality_grade', params.quality_grade);
  if (params?.max_price) query.append('max_price', String(params.max_price));
  if (params?.min_quantity) query.append('min_quantity', String(params.min_quantity));
  if (params?.status) query.append('status', params.status);

  const res = await api.get<ProduceListingItem[]>(`/market/listings?${query.toString()}`);
  return res.data;
};

export const fetchFarmerListings = async (farmer_id: string): Promise<ProduceListingItem[]> => {
  const res = await api.get<ProduceListingItem[]>(`/market/farmers/${farmer_id}/listings`, {
    headers: { 'x-farmer-id': farmer_id },
  });
  return res.data;
};

export const createProduceListing = async (
  farmer_id: string,
  payload: {
    crop_id: string;
    quantity: number;
    unit: string;
    quality_grade: string;
    expected_price: number;
    location: string;
  }
): Promise<any> => {
  const res = await api.post('/market/listings', payload, {
    headers: { 'x-farmer-id': farmer_id },
  });
  return res.data;
};

// ==============================================================================
// 3. Buyer Offers & Farmer Negotiation Endpoints
// ==============================================================================

export const submitBuyerOffer = async (
  listing_id: string,
  buyer_id: string,
  payload: {
    offered_price: number;
    quantity: number;
    message?: string;
  }
): Promise<any> => {
  const res = await api.post(`/market/listings/${listing_id}/offers`, payload, {
    headers: { 'x-farmer-id': buyer_id },
  });
  return res.data;
};

export const fetchListingOffers = async (listing_id: string, farmer_id: string): Promise<BuyerOfferItem[]> => {
  const res = await api.get<BuyerOfferItem[]>(`/market/listings/${listing_id}/offers`, {
    headers: { 'x-farmer-id': farmer_id },
  });
  return res.data;
};

export const fetchBuyerOffers = async (buyer_id: string): Promise<BuyerOfferItem[]> => {
  const res = await api.get<BuyerOfferItem[]>(`/market/buyers/${buyer_id}/offers`, {
    headers: { 'x-farmer-id': buyer_id },
  });
  return res.data;
};

export const respondToOffer = async (
  offer_id: string,
  farmer_id: string,
  action: 'ACCEPT' | 'REJECT',
  notes?: string
): Promise<any> => {
  const res = await api.post(
    `/market/offers/${offer_id}/respond`,
    { action, notes },
    { headers: { 'x-farmer-id': farmer_id } }
  );
  return res.data;
};

// ==============================================================================
// 4. Payment Gateway & Transaction Endpoints
// ==============================================================================

export const createPaymentOrder = async (
  buyer_id: string,
  offer_id: string,
  idempotency_key?: string
): Promise<PaymentOrderResponse> => {
  const res = await api.post<PaymentOrderResponse>(
    '/market/payments/create-order',
    { offer_id, idempotency_key },
    { headers: { 'x-farmer-id': buyer_id } }
  );
  return res.data;
};

export const verifyPaymentSignature = async (
  buyer_id: string,
  payload: {
    transaction_id: string;
    razorpay_order_id?: string;
    razorpay_payment_id?: string;
    razorpay_signature?: string;
    payu_txnid?: string;
    payu_payment_id?: string;
    payu_status?: string;
    payu_hash?: string;
    raw_payload?: Record<string, any>;
  }
): Promise<TransactionDetail> => {
  const res = await api.post<TransactionDetail>('/market/payments/verify', payload, {
    headers: { 'x-farmer-id': buyer_id },
  });
  return res.data;
};

export const fetchTransactionDetail = async (transaction_id: string, user_id: string): Promise<TransactionDetail> => {
  const res = await api.get<TransactionDetail>(`/market/payments/transactions/${transaction_id}`, {
    headers: { 'x-farmer-id': user_id },
  });
  return res.data;
};

export const fetchMyTransactions = async (user_id: string): Promise<TransactionDetail[]> => {
  const res = await api.get<TransactionDetail[]>('/market/payments/my-transactions', {
    headers: { 'x-farmer-id': user_id },
  });
  return res.data;
};
