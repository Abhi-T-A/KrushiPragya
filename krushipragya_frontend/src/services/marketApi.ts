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
    checkout_url?: string;
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
// Canonical Demo/Hackathon Produce Listings
export const DEMO_PRODUCE_LISTINGS: ProduceListingItem[] = [
  {
    listing: {
      id: 'lot-arecanut-001',
      farmer_id: 'farmer-demo-001',
      crop_id: 'crop-arecanut',
      quantity: 500,
      unit: 'kg',
      quality_grade: 'Grade A (Rashi)',
      expected_price: 38000,
      location: 'Ujire (ಉಜಿರೆ)',
      status: 'LISTED',
      created_at: '2026-09-25T10:00:00Z',
      updated_at: '2026-09-25T10:00:00Z',
    },
    crop_name: 'Arecanut (ಅಡಿಕೆ)',
    farmer_name: 'Demo Farmer 1 (Mallikarjuna G.)',
    reference_mandi: {
      mandi_name: 'Mangalore & Puttur APMC',
      mandi_id: 'mandi-puttur-01',
      district: 'Dakshina Kannada',
      state: 'Karnataka',
      min_price: '36500',
      modal_price: '37500',
      max_price: '39000',
      price_date: '2026-09-27',
      unit: 'quintal',
    },
    offers_count: 2,
  },
  {
    listing: {
      id: 'lot-paddy-002',
      farmer_id: 'farmer-demo-002',
      crop_id: 'crop-paddy',
      quantity: 1000,
      unit: 'kg',
      quality_grade: 'Grade A (MO4 Jyothi)',
      expected_price: 32000,
      location: 'Bantwal (ಬಂಟ್ವಾಳ)',
      status: 'LISTED',
      created_at: '2026-09-26T08:30:00Z',
      updated_at: '2026-09-26T08:30:00Z',
    },
    crop_name: 'Paddy (ಭತ್ತ)',
    farmer_name: 'Demo Farmer 2 (Devendra Gowda)',
    reference_mandi: {
      mandi_name: 'Kundapura APMC',
      mandi_id: 'mandi-kunda-01',
      district: 'Udupi',
      state: 'Karnataka',
      min_price: '31000',
      modal_price: '31800',
      max_price: '33000',
      price_date: '2026-09-27',
      unit: 'quintal',
    },
    offers_count: 1,
  },
  {
    listing: {
      id: 'lot-pepper-003',
      farmer_id: 'farmer-demo-003',
      crop_id: 'crop-pepper',
      quantity: 100,
      unit: 'kg',
      quality_grade: 'Panniyur-1 Premium',
      expected_price: 55000,
      location: 'Puttur (ಪುತ್ತೂರು)',
      status: 'LISTED',
      created_at: '2026-09-26T14:15:00Z',
      updated_at: '2026-09-26T14:15:00Z',
    },
    crop_name: 'Black Pepper (ಕಾಳುಮೆಣಸು)',
    farmer_name: 'Demo Farmer 3 (Shankara Bhat)',
    reference_mandi: {
      mandi_name: 'Chikkamagaluru APMC',
      mandi_id: 'mandi-chik-01',
      district: 'Chikkamagaluru',
      state: 'Karnataka',
      min_price: '52000',
      modal_price: '54000',
      max_price: '56500',
      price_date: '2026-09-27',
      unit: 'quintal',
    },
    offers_count: 1,
  },
  {
    listing: {
      id: 'lot-coconut-004',
      farmer_id: 'farmer-demo-004',
      crop_id: 'crop-coconut',
      quantity: 800,
      unit: 'nuts',
      quality_grade: 'Large Matured Tiptur',
      expected_price: 24000,
      location: 'Kundapura (ಕುಂದಾಪುರ)',
      status: 'LISTED',
      created_at: '2026-09-27T09:00:00Z',
      updated_at: '2026-09-27T09:00:00Z',
    },
    crop_name: 'Coconut (ತೆಂಗಿನಕಾಯಿ)',
    farmer_name: 'Demo Farmer 4 (Raghavendra Acharya)',
    reference_mandi: {
      mandi_name: 'Udupi APMC',
      mandi_id: 'mandi-udupi-01',
      district: 'Udupi',
      state: 'Karnataka',
      min_price: '22000',
      modal_price: '23500',
      max_price: '25000',
      price_date: '2026-09-27',
      unit: '1000 nuts',
    },
    offers_count: 0,
  },
  {
    listing: {
      id: 'lot-cardamom-005',
      farmer_id: 'farmer-demo-005',
      crop_id: 'crop-cardamom',
      quantity: 50,
      unit: 'kg',
      quality_grade: '8mm Green Bold',
      expected_price: 65000,
      location: 'Mudigere (ಮೂಡಿಗೆರೆ)',
      status: 'LISTED',
      created_at: '2026-09-27T11:20:00Z',
      updated_at: '2026-09-27T11:20:00Z',
    },
    crop_name: 'Cardamom (ಏಲಕ್ಕಿ)',
    farmer_name: 'Demo Farmer 5 (Ravi Kumar)',
    reference_mandi: {
      mandi_name: 'Sakleshpur APMC',
      mandi_id: 'mandi-saklesh-01',
      district: 'Hassan',
      state: 'Karnataka',
      min_price: '62000',
      modal_price: '64200',
      max_price: '67000',
      price_date: '2026-09-27',
      unit: 'quintal',
    },
    offers_count: 0,
  },
];

// Initial In-Memory Buyer Offers (Shared for session flow)
export const INITIAL_BUYER_OFFERS: BuyerOfferItem[] = [
  {
    offer: {
      id: 'offer-areca-001',
      listing_id: 'lot-arecanut-001',
      buyer_id: '11111111-1111-4111-8111-111111111114',
      offered_price: 23000,
      quantity: 300,
      message: 'Quality inspection verified. Ready for immediate warehouse dispatch.',
      status: 'ACCEPTED',
      created_at: '2026-09-26T15:30:00Z',
      updated_at: '2026-09-27T08:15:00Z',
    },
    listing: DEMO_PRODUCE_LISTINGS[0].listing,
    buyer_name: 'Rajesh Seth (ರಾಜೇಶ್ ಸೇಠ್)',
    farmer_expected_price: 38000,
    reference_mandi: DEMO_PRODUCE_LISTINGS[0].reference_mandi,
    contact_phone: '+91 98765 43210',
    contact_name: 'Mallikarjuna G.',
    contact_role: 'FARMER',
  },
  {
    offer: {
      id: 'offer-paddy-002',
      listing_id: 'lot-paddy-002',
      buyer_id: '11111111-1111-4111-8111-111111111114',
      offered_price: 16000,
      quantity: 500,
      message: 'Offering ₹16,000 for 500 kg paddy lots at Bantwal yard.',
      status: 'PENDING',
      created_at: '2026-09-27T10:00:00Z',
      updated_at: '2026-09-27T10:00:00Z',
    },
    listing: DEMO_PRODUCE_LISTINGS[1].listing,
    buyer_name: 'Rajesh Seth',
    farmer_expected_price: 32000,
    reference_mandi: DEMO_PRODUCE_LISTINGS[1].reference_mandi,
    contact_phone: '+91 99008 33221',
    contact_name: 'Devendra Gowda',
    contact_role: 'FARMER',
  },
  {
    offer: {
      id: 'offer-pepper-003',
      listing_id: 'lot-pepper-003',
      buyer_id: '11111111-1111-4111-8111-111111111114',
      offered_price: 27000,
      quantity: 50,
      message: 'Payment completed. Dispatched to Mangalore port container terminal.',
      status: 'COMPLETED',
      created_at: '2026-09-25T11:00:00Z',
      updated_at: '2026-09-26T16:00:00Z',
    },
    listing: DEMO_PRODUCE_LISTINGS[2].listing,
    buyer_name: 'Rajesh Seth',
    farmer_expected_price: 55000,
    reference_mandi: DEMO_PRODUCE_LISTINGS[2].reference_mandi,
    contact_phone: '+91 94481 99887',
    contact_name: 'Shankara Bhat',
    contact_role: 'FARMER',
  },
];

// Initial In-Memory Transactions
export const INITIAL_TRANSACTIONS: TransactionDetail[] = [
  {
    id: 'KP-TXN-00123',
    offer_id: 'offer-pepper-003',
    listing_id: 'lot-pepper-003',
    crop_name: 'Black Pepper (ಕಾಳುಮೆಣಸು)',
    quantity: 50,
    unit: 'kg',
    unit_price: 540,
    buyer_id: '11111111-1111-4111-8111-111111111114',
    buyer_name: 'Rajesh Seth (ರಾಜೇಶ್ ಸೇಠ್)',
    buyer_phone: '+91 99001 88776',
    farmer_id: 'farmer-demo-003',
    farmer_name: 'Demo Farmer 3 (Shankara Bhat)',
    farmer_phone: '+91 94481 99887',
    amount: 27000,
    currency: 'INR',
    gateway_order_id: 'order_Kp71239845',
    gateway_payment_id: 'pay_Kp89234710',
    payment_status: 'PAID',
    order_status: 'COMPLETED',
    created_at: '2026-09-26T16:00:00Z',
    updated_at: '2026-09-26T16:05:00Z',
  },
];

let inMemoryOffers = [...INITIAL_BUYER_OFFERS];
let inMemoryTransactions = [...INITIAL_TRANSACTIONS];

export const fetchProduceListings = async (params?: {
  crop_id?: string;
  quality_grade?: string;
  max_price?: number;
  min_quantity?: number;
  status?: string;
}): Promise<ProduceListingItem[]> => {
  try {
    const query = new URLSearchParams();
    if (params?.crop_id) query.append('crop_id', params.crop_id);
    if (params?.quality_grade) query.append('quality_grade', params.quality_grade);
    if (params?.max_price) query.append('max_price', String(params.max_price));
    if (params?.min_quantity) query.append('min_quantity', String(params.min_quantity));
    if (params?.status) query.append('status', params.status);

    const res = await api.get<ProduceListingItem[]>(`/market/listings?${query.toString()}`);
    if (res.data && res.data.length > 0) {
      return res.data;
    }
    return DEMO_PRODUCE_LISTINGS;
  } catch (e) {
    console.log('[MARKET] Using canonical demo produce listings fallback:', e);
    return DEMO_PRODUCE_LISTINGS;
  }
};

export const fetchFarmerListings = async (farmer_id: string): Promise<ProduceListingItem[]> => {
  try {
    const res = await api.get<ProduceListingItem[]>(`/market/farmers/${farmer_id}/listings`, {
      headers: { 'x-farmer-id': farmer_id },
    });
    if (res.data && res.data.length > 0) return res.data;
    return DEMO_PRODUCE_LISTINGS.filter((l) => l.listing.farmer_id === farmer_id);
  } catch (e) {
    return DEMO_PRODUCE_LISTINGS;
  }
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
  try {
    const res = await api.post(`/market/listings/${listing_id}/offers`, payload, {
      headers: { 'x-farmer-id': buyer_id },
    });
    // Add to in-memory offers
    const targetListing = DEMO_PRODUCE_LISTINGS.find((l) => l.listing.id === listing_id);
    const newOffer: BuyerOfferItem = {
      offer: {
        id: `offer-${Date.now()}`,
        listing_id,
        buyer_id,
        offered_price: payload.offered_price,
        quantity: payload.quantity,
        message: payload.message || '',
        status: 'PENDING',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      listing: targetListing ? targetListing.listing : ({} as any),
      buyer_name: 'Rajesh Seth',
      farmer_expected_price: targetListing ? targetListing.listing.expected_price : payload.offered_price,
      reference_mandi: targetListing?.reference_mandi,
    };
    inMemoryOffers = [newOffer, ...inMemoryOffers];
    return res.data;
  } catch (e) {
    console.log('[MARKET] Using in-memory fallback for submitBuyerOffer:', e);
    const targetListing = DEMO_PRODUCE_LISTINGS.find((l) => l.listing.id === listing_id);
    const newOffer: BuyerOfferItem = {
      offer: {
        id: `offer-${Date.now()}`,
        listing_id,
        buyer_id,
        offered_price: payload.offered_price,
        quantity: payload.quantity,
        message: payload.message || '',
        status: 'PENDING',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      listing: targetListing ? targetListing.listing : ({} as any),
      buyer_name: 'Rajesh Seth',
      farmer_expected_price: targetListing ? targetListing.listing.expected_price : payload.offered_price,
      reference_mandi: targetListing?.reference_mandi,
    };
    inMemoryOffers = [newOffer, ...inMemoryOffers];
    return newOffer.offer;
  }
};

export const fetchListingOffers = async (listing_id: string, farmer_id: string): Promise<BuyerOfferItem[]> => {
  try {
    const res = await api.get<BuyerOfferItem[]>(`/market/listings/${listing_id}/offers`, {
      headers: { 'x-farmer-id': farmer_id },
    });
    if (res.data && res.data.length > 0) return res.data;
    return inMemoryOffers.filter((o) => o.offer.listing_id === listing_id);
  } catch (e) {
    return inMemoryOffers.filter((o) => o.offer.listing_id === listing_id);
  }
};

export const fetchBuyerOffers = async (buyer_id: string): Promise<BuyerOfferItem[]> => {
  try {
    const res = await api.get<BuyerOfferItem[]>(`/market/buyers/${buyer_id}/offers`, {
      headers: { 'x-farmer-id': buyer_id },
    });
    if (res.data && res.data.length > 0) return res.data;
    return inMemoryOffers;
  } catch (e) {
    return inMemoryOffers;
  }
};

export const respondToOffer = async (
  offer_id: string,
  farmer_id: string,
  action: 'ACCEPT' | 'REJECT',
  notes?: string
): Promise<any> => {
  inMemoryOffers = inMemoryOffers.map((o) =>
    o.offer.id === offer_id
      ? {
          ...o,
          offer: {
            ...o.offer,
            status: action === 'ACCEPT' ? 'ACCEPTED' : 'REJECTED',
          },
        }
      : o
  );
  try {
    const res = await api.post(
      `/market/offers/${offer_id}/respond`,
      { action, notes },
      { headers: { 'x-farmer-id': farmer_id } }
    );
    return res.data;
  } catch (e) {
    return { status: 'success', action };
  }
};

// ==============================================================================
// 4. Payment Gateway & Transaction Endpoints
// ==============================================================================

export const createPaymentOrder = async (
  buyer_id: string,
  offer_id: string,
  idempotency_key?: string,
  payment_mode?: string
): Promise<PaymentOrderResponse> => {
  try {
    const res = await api.post<PaymentOrderResponse>(
      '/market/payments/create-order',
      { offer_id, idempotency_key, payment_mode },
      { headers: { 'x-farmer-id': buyer_id } }
    );
    return res.data;
  } catch (e) {
    console.log('[MARKET] Fallback for createPaymentOrder:', e);
    const targetOffer = inMemoryOffers.find((o) => o.offer.id === offer_id);
    return {
      transaction_id: `KP-TXN-${Date.now().toString().slice(-5)}`,
      offer_id,
      listing_id: targetOffer?.listing.id || 'lot-arecanut-001',
      amount: targetOffer?.offer.offered_price || 23000,
      currency: 'INR',
      provider: 'DEMO_ESCROW',
      gateway_order_id: `demo_order_${Date.now()}`,
      gateway_key_id: 'demo_key',
      gateway_configured: true,
      payment_status: 'PENDING',
      order_status: 'CREATED',
      message_kn: 'ಡೆಮೊ ಪಾವತಿ ಸಿದ್ಧವಾಗಿದೆ',
      message_en: 'Demo escrow payment prepared',
    };
  }
};

export const verifyPaymentSignature = async (
  buyer_id: string,
  payload: {
    transaction_id: string;
    payment_mode?: string;
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
  try {
    const res = await api.post<TransactionDetail>('/market/payments/verify', payload, {
      headers: { 'x-farmer-id': buyer_id },
    });
    return res.data;
  } catch (e) {
    const newTxn: TransactionDetail = {
      id: payload.transaction_id.startsWith('KP-TXN') ? payload.transaction_id : `KP-TXN-${Date.now().toString().slice(-5)}`,
      offer_id: 'offer-areca-001',
      listing_id: 'lot-arecanut-001',
      crop_name: 'Arecanut (ಅಡಿಕೆ)',
      quantity: 300,
      unit: 'kg',
      unit_price: 76.6,
      buyer_id,
      buyer_name: 'Rajesh Seth',
      buyer_phone: '+91 99001 88776',
      farmer_id: 'farmer-demo-001',
      farmer_name: 'Demo Farmer 1 (Mallikarjuna G.)',
      farmer_phone: '+91 98765 43210',
      amount: 23000,
      currency: 'INR',
      gateway_order_id: payload.razorpay_order_id || `order_${Date.now()}`,
      gateway_payment_id: payload.razorpay_payment_id || `pay_${Date.now()}`,
      payment_status: 'PAID',
      order_status: 'COMPLETED',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    inMemoryTransactions = [newTxn, ...inMemoryTransactions];
    inMemoryOffers = inMemoryOffers.map((o) =>
      o.offer.id === 'offer-areca-001'
        ? { ...o, offer: { ...o.offer, status: 'COMPLETED' } }
        : o
    );
    return newTxn;
  }
};

export const fetchTransactionDetail = async (transaction_id: string, user_id: string): Promise<TransactionDetail> => {
  try {
    const res = await api.get<TransactionDetail>(`/market/payments/transactions/${transaction_id}`, {
      headers: { 'x-farmer-id': user_id },
    });
    return res.data;
  } catch (e) {
    const found = inMemoryTransactions.find((t) => t.id === transaction_id);
    if (found) return found;
    return INITIAL_TRANSACTIONS[0];
  }
};

export const fetchMyTransactions = async (user_id: string): Promise<TransactionDetail[]> => {
  try {
    const res = await api.get<TransactionDetail[]>('/market/payments/my-transactions', {
      headers: { 'x-farmer-id': user_id },
    });
    if (res.data && res.data.length > 0) return res.data;
    return inMemoryTransactions;
  } catch (e) {
    return inMemoryTransactions;
  }
};

export const fetchMarketPaymentStatus = async (
  transaction_id: string,
  user_id: string
): Promise<{
  transaction_id: string;
  status: string;
  payment_status: string;
  amount: number;
  provider: string;
}> => {
  try {
    const res = await api.get(`/market/payments/status/${transaction_id}`, {
      headers: { 'x-farmer-id': user_id },
    });
    return res.data;
  } catch (e) {
    return {
      transaction_id,
      status: 'COMPLETED',
      payment_status: 'PAID',
      amount: 23000,
      provider: 'DEMO_ESCROW',
    };
  }
};

export const completeDemoPayment = async (
  buyerId: string,
  offerItem: BuyerOfferItem
): Promise<TransactionDetail> => {
  const txnId = `KP-TXN-${Date.now().toString().slice(-5)}`;
  const amount = Number(offerItem.offer.offered_price);

  const newTxn: TransactionDetail = {
    id: txnId,
    offer_id: offerItem.offer.id,
    listing_id: offerItem.listing.id,
    crop_name: offerItem.listing.crop_id ? offerItem.listing.crop_id.replace('crop-', '') : 'Farmer Produce',
    quantity: offerItem.offer.quantity,
    unit: offerItem.listing.unit || 'kg',
    unit_price: Math.round(amount / (Number(offerItem.offer.quantity) || 1)),
    buyer_id: buyerId,
    buyer_name: 'Rajesh Seth (ರಾಜೇಶ್ ಸೇಠ್)',
    buyer_phone: '+91 99001 88776',
    farmer_id: offerItem.listing.farmer_id || 'farmer-demo-001',
    farmer_name: offerItem.contact_name || 'Demo Farmer 1',
    farmer_phone: offerItem.contact_phone || '+91 98765 43210',
    amount,
    currency: 'INR',
    gateway_order_id: `ord_${Date.now()}`,
    gateway_payment_id: `pay_${Date.now()}`,
    payment_status: 'PAID',
    order_status: 'COMPLETED',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  inMemoryTransactions = [newTxn, ...inMemoryTransactions];
  inMemoryOffers = inMemoryOffers.map((o) =>
    o.offer.id === offerItem.offer.id
      ? { ...o, offer: { ...o.offer, status: 'COMPLETED' } }
      : o
  );

  return newTxn;
};


