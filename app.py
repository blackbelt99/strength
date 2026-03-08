from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json, os, socket, re, time

app = Flask(__name__)
app.secret_key = 'strengthcloud_ultra_secret_2024'

PLANS_FILE    = 'plans.json'
USERS_FILE    = 'users.json'
ORDERS_FILE   = 'orders.json'
SETTINGS_FILE = 'settings.json'

MAIN_ADMIN_EMAIL = "gyt61039@gmail.com"
MAIN_ADMIN_PASS  = "saim5454"
MAIN_ADMIN_USER  = {
    "email":    MAIN_ADMIN_EMAIL,
    "username": "MainAdmin",
    "password": MAIN_ADMIN_PASS,
    "role":     "main_admin"
}

DEFAULT_PLANS = {
    "minecraft": [
        {"name":"Dirt Plan",     "ram":"2GB",  "cpu":"80%",  "storage":"8GB NVMe SSD",  "database":"Unlimited","price":59, "color":"#8B4513"},
        {"name":"Wooden Plan",   "ram":"4GB",  "cpu":"100%", "storage":"10GB NVMe SSD", "database":"Unlimited","price":99, "color":"#DEB887"},
        {"name":"Stone Plan",    "ram":"6GB",  "cpu":"150%", "storage":"15GB NVMe SSD", "database":"Unlimited","price":199,"color":"#808080"},
        {"name":"Iron Plan",     "ram":"8GB",  "cpu":"200%", "storage":"20GB NVMe SSD", "database":"Unlimited","price":299,"color":"#C0C0C0","popular":True},
        {"name":"Emerald Plan",  "ram":"12GB", "cpu":"250%", "storage":"25GB NVMe SSD", "database":"Unlimited","price":399,"color":"#50C878"},
        {"name":"Diamond Plan",  "ram":"16GB", "cpu":"300%", "storage":"30GB NVMe SSD", "database":"Unlimited","price":499,"color":"#00BFFF"},
        {"name":"Netherite Plan","ram":"20GB", "cpu":"300%", "storage":"40GB NVMe SSD", "database":"Unlimited","price":599,"color":"#4A4A4A"},
        {"name":"Titanium Plan", "ram":"32GB", "cpu":"400%", "storage":"50GB NVMe SSD", "database":"Unlimited","price":999,"color":"#9932CC"},
    ],
    "vps": [
        {"name":"Starter VPS","ram":"2GB","cpu":"2 vCPU","storage":"20GB NVMe SSD","bandwidth":"1TB","price":199,"color":"#4169E1"},
        {"name":"Pro VPS",    "ram":"4GB","cpu":"4 vCPU","storage":"40GB NVMe SSD","bandwidth":"2TB","price":399,"color":"#1E90FF","popular":True},
        {"name":"Elite VPS",  "ram":"8GB","cpu":"6 vCPU","storage":"80GB NVMe SSD","bandwidth":"4TB","price":799,"color":"#00CED1"},
    ]
}

DEFAULT_SETTINGS = {
    "site_name":"StrengthCloud",
    "discord_url":"https://discord.gg/strengthcloud",
    "client_panel_url":"https://panel.strengthcloud.com",
    "support_email":"support@strengthcloud.com",
    "currency":"rupee",
}

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f: return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w') as f: json.dump(data, f, indent=2)

def load_plans():    return load_json(PLANS_FILE,    DEFAULT_PLANS)
def save_plans(p):   save_json(PLANS_FILE, p)
def load_users():    return load_json(USERS_FILE,    [])
def save_users(u):   save_json(USERS_FILE, u)
def load_orders():   return load_json(ORDERS_FILE,   [])
def save_orders(o):  save_json(ORDERS_FILE, o)
def load_settings(): return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
def save_settings(s):save_json(SETTINGS_FILE, s)

def get_current_user():
    return session.get('user', None)

def is_admin():
    u = get_current_user()
    if not u: return False
    return (u.get('email') == MAIN_ADMIN_EMAIL or
            u.get('role') in ('admin', 'main_admin'))

def is_main_admin():
    u = get_current_user()
    return bool(u and u.get('email') == MAIN_ADMIN_EMAIL)

def check_domain_available(domain):
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True
    except Exception:
        return None

# ── inject is_admin_user into EVERY template automatically ────────────────────
# This means your base.html can use {{ is_admin_user }} without any HTML changes
@app.context_processor
def inject_globals():
    u = get_current_user()
    admin = False
    if u:
        admin = (u.get('email') == MAIN_ADMIN_EMAIL or
                 u.get('role') in ('admin', 'main_admin'))
    return {
        'is_admin_user': admin,
        'current_user':  u,
    }

def ctx(**kwargs):
    base = {
        'user':       get_current_user(),
        'cart_count': len(session.get('cart', [])),
        'settings':   load_settings(),
    }
    base.update(kwargs)
    return base

# ── pages ──────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html', **ctx())

@app.route('/minecraft-hosting')
def minecraft_hosting():
    return render_template('minecraft.html', plans=load_plans()['minecraft'], **ctx())

@app.route('/vps')
def vps_page():
    return render_template('vps.html', plans=load_plans()['vps'], **ctx())

@app.route('/domains')
def domains_page():
    return render_template('domains.html', **ctx())

@app.route('/cart')
def cart():
    return render_template('cart.html', **ctx())

@app.route('/support')
def support():
    return render_template('support.html', **ctx())

# ── api ────────────────────────────────────────────────────────────────────────
@app.route('/api/check-domain')
def check_domain():
    domain = request.args.get('domain', '').strip().lower()
    if not domain:
        return jsonify({'error': 'No domain'}), 400
    if not re.match(r'^[a-z0-9][a-z0-9\-]{0,61}[a-z0-9]?\.[a-z]{2,}$', domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    return jsonify({'domain': domain, 'available': check_domain_available(domain)})

@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = request.json
    cart = session.get('cart', [])
    for item in cart:
        if item['name'] == data['name'] and item['type'] == data['type']:
            return jsonify({'success': True, 'message': 'Already in cart', 'count': len(cart)})
    cart.append(data)
    session['cart'] = cart
    return jsonify({'success': True, 'count': len(cart)})

@app.route('/api/cart/remove', methods=['POST'])
def cart_remove():
    data = request.json
    cart = session.get('cart', [])
    cart = [i for i in cart if not (i['name'] == data['name'] and i['type'] == data['type'])]
    session['cart'] = cart
    return jsonify({'success': True, 'count': len(cart)})

@app.route('/api/cart/items')
def cart_items():
    return jsonify({'items': session.get('cart', [])})

@app.route('/checkout', methods=['POST'])
def checkout():
    if not get_current_user(): return redirect(url_for('login'))
    cart = session.get('cart', [])
    if not cart: return redirect(url_for('cart'))
    orders = load_orders()
    order = {
        'id':       f"SC{int(time.time())}",
        'user':     get_current_user()['email'],
        'username': get_current_user()['username'],
        'items':    cart,
        'total':    sum(i['price'] for i in cart),
        'status':   'pending',
        'created':  time.strftime('%Y-%m-%d %H:%M:%S')
    }
    orders.append(order)
    save_orders(orders)
    session['cart'] = []
    return render_template('checkout_success.html', order=order, **ctx())

# ── auth ───────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Hardcoded main admin — no registration needed ever
        if email == MAIN_ADMIN_EMAIL and password == MAIN_ADMIN_PASS:
            session['user'] = MAIN_ADMIN_USER
            return redirect(url_for('admin'))

        users = load_users()
        user  = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if user:
            session['user'] = user
            if user.get('role') in ('admin', 'main_admin'):
                return redirect(url_for('admin'))
            return redirect(url_for('home'))

        return render_template('login.html', error='Invalid email or password', **ctx())
    return render_template('login.html', **ctx())

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if email == MAIN_ADMIN_EMAIL:
            return render_template('signup.html', error='This email is reserved.', **ctx())
        if password != confirm:
            return render_template('signup.html', error='Passwords do not match', **ctx())
        users = load_users()
        if any(u['email'] == email for u in users):
            return render_template('signup.html', error='Email already registered', **ctx())
        new_user = {'email': email, 'username': username, 'password': password, 'role': 'user'}
        users.append(new_user)
        save_users(users)
        session['user'] = new_user
        return redirect(url_for('home'))
    return render_template('signup.html', **ctx())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ── admin ──────────────────────────────────────────────────────────────────────
@app.route('/admin')
def admin():
    if not is_admin(): return redirect(url_for('login'))
    return render_template('admin.html',
        plans=load_plans(),
        users=load_users(),
        orders=load_orders(),
        settings=load_settings(),
        user=get_current_user(),
        is_main_admin=is_main_admin(),
        main_admin_email=MAIN_ADMIN_EMAIL,
        cart_count=0)

@app.route('/admin/update_plan', methods=['POST'])
def update_plan():
    if not is_admin(): return jsonify({'error': 'Unauthorized'}), 401
    data  = request.json
    plans = load_plans()
    cat, idx, pd = data.get('category'), data.get('index'), data.get('plan')
    if cat in plans and 0 <= idx < len(plans[cat]):
        plans[cat][idx].update(pd)
        save_plans(plans)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid'}), 400

@app.route('/admin/add_plan', methods=['POST'])
def add_plan():
    if not is_admin(): return jsonify({'error': 'Unauthorized'}), 401
    data  = request.json
    plans = load_plans()
    cat   = data.get('category')
    if cat in plans:
        plans[cat].append(data.get('plan'))
        save_plans(plans)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid'}), 400

@app.route('/admin/delete_plan', methods=['POST'])
def delete_plan():
    if not is_admin(): return jsonify({'error': 'Unauthorized'}), 401
    data  = request.json
    plans = load_plans()
    cat, idx = data.get('category'), data.get('index')
    if cat in plans and 0 <= idx < len(plans[cat]):
        plans[cat].pop(idx)
        save_plans(plans)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid'}), 400

@app.route('/admin/make_admin', methods=['POST'])
def make_admin():
    if not is_main_admin(): return jsonify({'error': 'Only main admin'}), 403
    email = request.json.get('email')
    users = load_users()
    for u in users:
        if u['email'] == email:
            u['role'] = 'admin'
            save_users(users)
            return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

@app.route('/admin/remove_admin', methods=['POST'])
def remove_admin():
    if not is_main_admin(): return jsonify({'error': 'Only main admin'}), 403
    email = request.json.get('email')
    if email == MAIN_ADMIN_EMAIL:
        return jsonify({'error': 'Cannot remove main admin'}), 403
    users = load_users()
    for u in users:
        if u['email'] == email:
            u['role'] = 'user'
            save_users(users)
            return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404

@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    if not is_admin(): return jsonify({'error': 'Unauthorized'}), 401
    settings = load_settings()
    settings.update(request.json)
    save_settings(settings)
    return jsonify({'success': True})

@app.route('/admin/update_order', methods=['POST'])
def update_order():
    if not is_admin(): return jsonify({'error': 'Unauthorized'}), 401
    data   = request.json
    orders = load_orders()
    for o in orders:
        if o['id'] == data['id']:
            o['status'] = data['status']
            save_orders(orders)
            return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)