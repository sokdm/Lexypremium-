from flask import render_template, request, redirect, url_for, flash, abort, send_from_directory, jsonify, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from app import app, db
from models import User, Product, ProductImage, Category, CartItem, Order, OrderItem, Notification, SiteSettings, MonnifyTransactionLog, Product
from forms import ProductForm, CategoryForm, OrderStatusForm, SettingsForm
from utils import save_image

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    
    recent_webhooks = MonnifyTransactionLog.query.order_by(MonnifyTransactionLog.created_at.desc()).limit(5).all()
    
    stats = {
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(payment_status='pending').count(),
        'paid_orders': Order.query.filter_by(payment_status='paid').count(),
        'total_products': Product.query.count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='paid').scalar() or 0,
        'recent_orders': Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        'recent_webhooks': recent_webhooks,
        'webhook_count': MonnifyTransactionLog.query.count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        abort(403)
    
    form = ProductForm()
    form.category_id.choices = [(0, 'No Category')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        base_slug = secure_filename(form.name.data.lower().replace(' ', '-'))
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        product = Product(
            name=form.name.data,
            slug=slug,
            price=form.price.data,
            original_price=form.original_price.data,
            length=form.length.data,
            description=form.description.data,
            short_description=form.short_description.data,
            stock=form.stock.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            is_featured=form.is_featured.data,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.flush()
        
        files = request.files.getlist('images')
        for i, file in enumerate(files):
            if file and file.filename:
                filename = save_image(file, f"product_{product.id}_")
                if filename:
                    img = ProductImage(
                        product_id=product.id,
                        filename=filename,
                        is_primary=(i == 0)
                    )
                    db.session.add(img)
        
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='Add Product')

@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(id):
    if not current_user.is_admin:
        abort(403)
    
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(0, 'No Category')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.original_price = form.original_price.data
        product.length = form.length.data
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data if form.category_id.data != 0 else None
        product.is_featured = form.is_featured.data
        product.is_active = form.is_active.data
        
        files = request.files.getlist('images')
        for i, file in enumerate(files):
            if file and file.filename:
                filename = save_image(file, f"product_{product.id}_")
                if filename:
                    img = ProductImage(
                        product_id=product.id,
                        filename=filename,
                        is_primary=(not product.images and i == 0)
                    )
                    db.session.add(img)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')

@app.route('/admin/product/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_product(id):
    if not current_user.is_admin:
        abort(403)
    
    product = Product.query.get_or_404(id)
    
    for img in product.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img.filename))
        except:
            pass
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    payment_status = request.args.get('payment_status')
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    if payment_status:
        query = query.filter_by(payment_status=payment_status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/orders.html', orders=orders, current_status=status, current_payment_status=payment_status)

@app.route('/admin/order/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_order_detail(id):
    if not current_user.is_admin:
        abort(403)
    
    order = Order.query.get_or_404(id)
    form = OrderStatusForm(obj=order)
    
    if form.validate_on_submit():
        old_payment_status = order.payment_status
        order.status = form.status.data
        order.payment_status = form.payment_status.data
        order.notes = form.notes.data
        
        if form.payment_status.data == 'paid' and old_payment_status != 'paid':
            order.paid_at = datetime.utcnow()
            
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock -= item.quantity
                    product.sold_count += item.quantity
            
            from monnify import create_notification
            create_notification(
                type='email',
                recipient=order.email,
                subject=f'Payment Confirmed - Order {order.order_number}',
                message=f'Your payment for order {order.order_number} has been confirmed.'
            )
        
        db.session.commit()
        flash('Order updated successfully!', 'success')
        return redirect(url_for('admin_orders'))
    
    return render_template('admin/order_detail.html', order=order, form=form)

@app.route('/admin/order/<int:id>/verify-monnify')
@login_required
def verify_monnify_payment(id):
    """Manually verify payment via Monnify API"""
    if not current_user.is_admin:
        abort(403)
    
    order = Order.query.get_or_404(id)
    
    if not order.monnify_transaction_reference:
        flash('No Monnify transaction reference found for this order.', 'error')
        return redirect(url_for('admin_order_detail', id=id))
    
    from monnify import MonnifyAPI
    monnify = MonnifyAPI()
    result = monnify.get_transaction_status(order.monnify_transaction_reference)
    
    if result['success']:
        if result['paid']:
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
                message=f'Your payment of ₦{result["amount"]} has been verified and confirmed.'
            )
            
            flash(f'Payment verified! Amount: ₦{result["amount"]}', 'success')
        else:
            flash(f'Payment not yet completed. Status: {result.get("data", {}).get("paymentStatus", "Unknown")}', 'warning')
    else:
        flash(f'Verification failed: {result.get("error", "Unknown error")}', 'error')
    
    return redirect(url_for('admin_order_detail', id=id))

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    if not current_user.is_admin:
        abort(403)
    
    form = CategoryForm()
    if form.validate_on_submit():
        slug = secure_filename(form.name.data.lower().replace(' ', '-'))
        category = Category(name=form.name.data, slug=slug, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added!', 'success')
        return redirect(url_for('admin_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories, form=form)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        abort(403)
    
    form = SettingsForm()
    
    if form.validate_on_submit():
        settings = {
            'store_name': form.store_name.data,
            'store_phone': form.store_phone.data,
            'store_email': form.store_email.data,
            'bank_name': form.bank_name.data,
            'bank_account': form.bank_account.data,
            'bank_account_name': form.bank_account_name.data
        }
        
        for key, value in settings.items():
            setting = SiteSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SiteSettings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('admin_settings'))
    
    if request.method == 'GET':
        form.store_name.data = SiteSettings.get_value('store_name', 'LuxeWigs NG')
        form.store_phone.data = SiteSettings.get_value('store_phone', '+2348108332873')
        form.store_email.data = SiteSettings.get_value('store_email', 'sokwilliams41@gmail.com')
        form.bank_name.data = SiteSettings.get_value('bank_name', '')
        form.bank_account.data = SiteSettings.get_value('bank_account', '')
        form.bank_account_name.data = SiteSettings.get_value('bank_account_name', '')
    
    return render_template('admin/settings.html', form=form)

@app.route('/admin/webhook-logs')
@login_required
def webhook_logs():
    """View Monnify webhook logs"""
    if not current_user.is_admin:
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    logs = MonnifyTransactionLog.query.order_by(MonnifyTransactionLog.created_at.desc()).paginate(page=page, per_page=50)
    
    return render_template('admin/webhook_logs.html', logs=logs)

# ==================== MONNIFY WEBHOOK ====================

@app.route('/webhook/monnify', methods=['POST'])
def monnify_webhook():
    """
    Monnify webhook endpoint - handles automatic payment notifications
    """
    try:
        event_data = request.get_json()
        
        print(f"Webhook received: {event_data}")
        
        # Log the webhook
        log = MonnifyTransactionLog(
            event_type=event_data.get('eventType', 'UNKNOWN'),
            payload=json.dumps(event_data),
            processed=False
        )
        db.session.add(log)
        db.session.commit()
        
        # Process successful transaction
        if event_data.get('eventType') == 'SUCCESSFUL_TRANSACTION':
            event_body = event_data.get('eventData', {})
            transaction_reference = event_body.get('transactionReference')
            payment_reference = event_body.get('paymentReference')
            payment_status = event_body.get('paymentStatus')
            amount_paid = event_body.get('amount', 0)
            
            # Find order
            order = Order.query.filter(
                db.or_(
                    Order.monnify_payment_reference == payment_reference,
                    Order.monnify_transaction_reference == transaction_reference
                )
            ).first()
            
            if order and payment_status == 'PAID':
                if float(amount_paid) >= float(order.total_amount) * 0.99:
                    
                    # Update order
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.paid_at = datetime.utcnow()
                    
                    # Update stock
                    for item in order.items:
                        product = Product.query.get(item.product_id)
                        if product:
                            product.stock -= item.quantity
                            product.sold_count += item.quantity
                    
                    # Notifications
                    from monnify import create_notification
                    
                    create_notification(
                        type='email',
                        recipient=order.email,
                        subject=f'Payment Confirmed - Order {order.order_number}',
                        message=f'Your payment of ₦{amount_paid} has been confirmed.'
                    )
                    
                    admin_msg = f"💰 NEW PAYMENT!\n\nOrder: #{order.order_number}\nAmount: ₦{amount_paid}\nCustomer: {order.full_name}"
                    create_notification(
                        type='whatsapp',
                        recipient=current_app.config['WHATSAPP_PHONE_NUMBER'],
                        message=admin_msg
                    )
                    
                    create_notification(
                        type='dashboard',
                        recipient='admin',
                        message=f'Payment received for order #{order.order_number}'
                    )
                    
                    log.processed = True
                    db.session.commit()
                    
                    print(f"✅ Order {order.order_number} auto-processed!")
                    return jsonify({'success': True, 'message': 'Payment processed'}), 200
        
        # Handle failed transaction
        elif event_data.get('eventType') == 'FAILED_TRANSACTION':
            payment_reference = event_body.get('paymentReference')
            order = Order.query.filter_by(monnify_payment_reference=payment_reference).first()
            
            if order:
                order.payment_status = 'failed'
                order.notes = f"Payment failed: {event_body.get('message', 'Unknown')}"
                db.session.commit()
        
        log.processed = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Event logged'}), 200
        
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES ====================

@app.route('/api/cart/count')
def cart_count():
    if current_user.is_authenticated:
        count = db.session.query(db.func.sum(CartItem.quantity)).filter_by(user_id=current_user.id).scalar() or 0
    else:
        count = sum(session.get('cart', {}).values())
    return jsonify({'count': int(count)})

@app.route('/api/order/<int:order_id>/status')
def check_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'status': order.status,
        'payment_status': order.payment_status,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None
    })

# ==================== STATIC FILES & ERRORS ====================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ==================== CLI COMMANDS ====================

@app.cli.command('init-db')
def init_db():
    """Initialize database with default data"""
    db.create_all()
    
    # Create default admin
    admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin:
        admin = User(
            email=app.config['ADMIN_EMAIL'],
            is_admin=True,
            full_name='Administrator'
        )
        db.session.add(admin)
    
    # Create default categories
    if not Category.query.first():
        categories = [
            Category(name='Bone Straight', slug='bone-straight', description='Premium bone straight wigs'),
            Category(name='Curly Hair', slug='curly-hair', description='Beautiful curly wigs'),
            Category(name='Body Wave', slug='body-wave', description='Elegant body wave styles'),
            Category(name='Deep Wave', slug='deep-wave', description='Gorgeous deep wave textures'),
            Category(name='Closure Wigs', slug='closure-wigs', description='Wigs with closure'),
            Category(name='Frontal Wigs', slug='frontal-wigs', description='Wigs with frontal')
        ]
        for cat in categories:
            db.session.add(cat)
    
    # Create default settings
    default_settings = {
        'store_name': 'LuxeWigs NG',
        'store_phone': '+2348108332873',
        'store_email': 'sokwilliams41@gmail.com',
        'bank_name': 'Monnify Virtual Bank',
        'bank_account': 'AUTO-GENERATED',
        'bank_account_name': 'LuxeWigs NG Enterprise'
    }
    
    for key, value in default_settings.items():
        if not SiteSettings.query.filter_by(key=key).first():
            db.session.add(SiteSettings(key=key, value=value))
    
    db.session.commit()
    print('✅ Database initialized successfully!')
