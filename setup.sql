-- 1. Products Table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    images TEXT[] DEFAULT '{}',
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id), -- Link to Supabase Auth User
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_address TEXT NOT NULL,
    customer_city TEXT NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Order Items Table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price_at_purchase NUMERIC(10, 2) NOT NULL
);

-- 4. Sample Data
INSERT INTO products (name, description, price, stock, category)
VALUES 
('Classic T-Shirt', 'A comfortable cotton t-shirt', 19.99, 100, 'Apparel'),
('Premium Hoodie', 'Warm and stylish hoodie', 49.99, 50, 'Apparel'),
('Leather Wallet', 'Handcrafted genuine leather wallet', 29.99, 30, 'Accessories');

-- 5. Enable RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- --- Products Policies ---
-- Allow anyone to view products
CREATE POLICY "Allow public read access" ON products
FOR SELECT USING (true);

-- Allow anyone to create/edit products for testing (In production, restrict to Admins)
CREATE POLICY "Allow all access for testing" ON products
FOR ALL USING (true) WITH CHECK (true);

-- --- Orders Policies ---
-- Users can only see their own orders
CREATE POLICY "Users can view their own orders" ON orders
FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own orders
CREATE POLICY "Users can create their own orders" ON orders
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Allow viewing order items if you own the order
CREATE POLICY "Users can view their own order items" ON order_items
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM orders 
    WHERE orders.id = order_items.order_id 
    AND orders.user_id = auth.uid()
  )
);
