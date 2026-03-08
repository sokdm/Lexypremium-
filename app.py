from dotenv import load_dotenv
import os
load_dotenv()

import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Product, ProductImage, Category, CartItem, Order, OrderItem, Notification, SiteSettings, MonnifyTransactionLog
from forms import LoginForm, ProductForm, CategoryForm, CheckoutForm, OrderStatusForm, SettingsForm
from utils import save_image, format_currency, generate_qr_code

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Template filters
@app.template_filter('currency')
def currency_filter(amount):
    return format_currency(amount)

@app.template_filter('datetime')
def datetime_filter(value):
    if value is None:
        return ''
    return value.strftime('%B %d, %Y at %I:%M %p')

# Context processors
@app.context_processor
def inject_settings():
    settings = {}
    for setting in SiteSettings.query.all():
        settings[setting.key] = setting.value
    return dict(settings=settings, current_year=datetime.now().year)

@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

# Routes - Main Pages
@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(4).all()
    categories = Category.query.all()
    return render_template('index.html', 
                         featured_products=featured_products,
                         new_arrivals=new_arrivals,
                         categories=categories)

@app.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(is_active=True)
    
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.sold_count.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()
    
    return render_template('shop.html', products=products, categories=categories, 
                         current_category=category_slug, search=search, sort=sort)

@app.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('product_detail.html', product=product, 
                         related_products=related_products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Cart Routes
@app.route('/cart')
def cart():
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    else:
        cart_items = []
        cart_data = session.get('cart', {})
        for product_id, qty in cart_data.items():
            product = Product.query.get(int(product_id))
            if product:
                cart_items.append({'product': product, 'quantity': qty, 'id': None})
    
    total = sum(item.product.price * item.quantity for item in cart_items) if cart_items else 0
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if product.stock < quantity:
        flash('Sorry, not enough stock available.', 'error')
        return redirect(url_for('product_detail', slug=product.slug))
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
    else:
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session['cart'] = cart
        session.modified = True
    
    flash(f'Added {product.name} to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = int(request.form.get('quantity', 1))
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            abort(403)
        
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        db.session.commit()
    else:
        cart = session.get('cart', {})
        product_id = str(item_id)
        if quantity <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = quantity
        session['cart'] = cart
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>')
def remove_from_cart(item_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            abort(403)
        db.session.delete(cart_item)
        db.session.commit()
    else:
        cart = session.get('cart', {})
        cart.pop(str(item_id), None)
        session['cart'] = cart
    
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# Checkout & Payment with Monnify
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    else:
        cart_items = []
        cart_data = session.get('cart', {})
        for pid, qty in cart_data.items():
            product = Product.query.get(int(pid))
            if product:
                cart_items.append(type('obj', (object,), {
                    'product': product, 
                    'quantity': qty,
                    'product_id': int(pid)
                })())
    
    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('shop'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    form = CheckoutForm()
    if form.validate_on_submit():
        # Create or update user
        if current_user.is_authenticated:
            user = current_user
        else:
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                user = User(
                    email=form.email.data,
                    phone=form.phone.data,
                    full_name=form.full_name.data,
                    address=form.address.data,
                    city=form.city.data,
                    state=form.state.data
                )
                db.session.add(user)
                db.session.commit()
        
        # Create order
        order = Order(
            user_id=user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            total_amount=total,
            payment_status='pending',
            status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id if hasattr(item, 'product_id') else item.product.id,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                length=item.product.length
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Import Monnify here to avoid circular import
        from monnify import MonnifyAPI
        monnify = MonnifyAPI()
        account_result = monnify.reserve_account(
            order=order,
            customer_email=form.email.data,
            customer_name=form.full_name.data
        )
        
        if account_result['success']:
            # Clear cart
            if current_user.is_authenticated:
                CartItem.query.filter_by(user_id=current_user.id).delete()
                db.session.commit()
            else:
                session.pop('cart', None)
            
            session['order_email'] = form.email.data
            
            flash('Order placed! Please complete payment using the account details.', 'success')
            return redirect(url_for('payment', order_id=order.id))
        else:
            db.session.delete(order)
            db.session.commit()
            flash(f'Payment setup failed: {account_result.get("error", "Unknown error")}. Please try again.', 'error')
            return redirect(url_for('checkout'))
    
    # Pre-fill form for logged-in users
    if current_user.is_authenticated and request.method == 'GET':
        form.full_name.data = current_user.full_name or ''
        form.email.data = current_user.email or ''
        form.phone.data = current_user.phone or ''
        form.address.data = current_user.address or ''
        form.city.data = current_user.city or ''
        form.state.data = current_user.state or ''
    
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)

@app.route('/payment/<int:order_id>')
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Security check
    if not current_user.is_authenticated or order.user_id != current_user.id:
        if order.email != session.get('order_email'):
            abort(403)
    
    # If already paid, redirect to confirmation
    if order.payment_status == 'paid':
        return redirect(url_for('order_confirmation', order_number=order.order_number))
    
    bank_details = {
        'bank_name': order.monnify_bank_name or 'Processing...',
        'account_number': order.monnify_account_number or 'Generating...',
        'account_name': order.monnify_account_name or f'LuxeWigs - {order.full_name[:20]}',
        'amount': order.total_amount,
        'order_number': order.order_number,
        'payment_reference': order.monnify_payment_reference or ''
    }
    
    qr_data = f"Bank:{bank_details['bank_name']}|Acc:{bank_details['account_number']}|Amount:{bank_details['amount']}"
    qr_code = generate_qr_code(qr_data)
    
    account_ready = all([order.monnify_account_number, order.monnify_bank_name])
    
    return render_template('payment.html', order=order, bank_details=bank_details, 
                         qr_code=qr_code, account_ready=account_ready)

@app.route('/payment/verify/<int:order_id>')
def verify_payment_status(order_id):
    """Manual verification endpoint"""
    order = Order.query.get_or_404(order_id)
    
    if order.monnify_transaction_reference:
        from monnify import MonnifyAPI
        monnify = MonnifyAPI()
        result = monnify.get_transaction_status(order.monnify_transaction_reference)
        
        if result['success'] and result['paid']:
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.status = 'processing'
                order.paid_at = datetime.utcnow()
                
                for item in order.items:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock -= item.quantity
                        product.sold_count += item.quantity
                
                db.session.commit()
                
                from monnify import create_notification
                create_notification(
                    type='email',
                    recipient=order.email,
                    subject=f'Payment Confirmed - Order {order.order_number}',
                    message=f'Your payment of ₦{order.total_amount} has been confirmed.'
                )
            
            return jsonify({
                'success': True,
                'status': 'paid',
                'redirect': url_for('order_confirmation', order_number=order.order_number)
            })
    
    return jsonify({
        'success': True,
        'status': order.payment_status,
        'pending': True
    })

@app.route('/order/confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_confirmation.html', order=order)

# Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check if admin login
        if form.email.data == app.config['ADMIN_EMAIL'] and form.password.data == app.config['ADMIN_PASSWORD']:
            if not user:
                user = User(
                    email=app.config['ADMIN_EMAIL'],
                    is_admin=True,
                    full_name='Admin'
                )
                db.session.add(user)
                db.session.commit()
            else:
                user.is_admin = True
                db.session.commit()
            login_user(user, remember=form.remember.data)
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Import admin routes and webhooks from separate file
from admin_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
