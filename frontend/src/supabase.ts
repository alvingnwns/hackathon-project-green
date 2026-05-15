import { createClient } from '@supabase/supabase-js';

// VITE_SUPABASE_URL has a known Vite 8 env parsing issue with URL values; URL is hardcoded as fallback (not a secret)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://tnfulriepkzquoafqidv.supabase.co';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key';

if (!supabaseKey || supabaseKey === 'placeholder-anon-key') {
  console.warn('[Supabase] API key not set — recent projects & history unavailable.');
}

export const supabase = createClient(supabaseUrl, supabaseKey);