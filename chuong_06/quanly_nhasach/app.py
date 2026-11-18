import os
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from forms import BookForm, CategoryForm, CheckoutForm
from models import Book, Category, Order, OrderItem, db


# 1. KHỞI TẠO ỨNG DỤNG & CẤU HÌNH
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "song-huong-bookstore-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'bookstore.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Tối đa 2 MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

FREE_SHIPPING_THRESHOLD = 200000
DEFAULT_SHIPPING_FEE = 20000
MAX_IMAGE_BYTES = 2 * 1024 * 1024


# 2. HÀM TIỆN ÍCH (SESSION GIỎ HÀNG, UPLOAD ẢNH, FILTER JINJA2)
def get_raw_cart():
    cart = session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
        session["cart"] = cart
    return cart


def get_cart_total_quantity():
    cart = get_raw_cart()
    return sum(int(qty) for qty in cart.values() if int(qty) > 0)


def get_cart_details():
    """Luôn lấy giá mới nhất từ CSDL, không lưu giá trong session."""
    cart = get_raw_cart()
    if not cart:
        return [], 0, 0, 0

    book_ids = [int(bid) for bid in cart.keys() if str(bid).isdigit()]
    books = Book.query.filter(Book.id.in_(book_ids)).all()
    book_map = {b.id: b for b in books}

    items = []
    subtotal = 0
    cleaned_cart = {}

    for bid_str, qty in cart.items():
        if not str(bid_str).isdigit():
            continue
        bid = int(bid_str)
        book = book_map.get(bid)
        qty = int(qty)
        if not book or qty <= 0:
            continue

        cleaned_cart[str(bid)] = qty
        line_total = book.price * qty
        subtotal += line_total
        items.append(
            {
                "book": book,
                "quantity": qty,
                "unit_price": book.price,
                "line_total": line_total,
            }
        )

    if cleaned_cart != cart:
        session["cart"] = cleaned_cart
        session.modified = True

    if not items:
        return [], 0, 0, 0

    shipping_fee = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else DEFAULT_SHIPPING_FEE
    grand_total = subtotal + shipping_fee
    return items, subtotal, shipping_fee, grand_total


def save_cover_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > MAX_IMAGE_BYTES:
        raise ValueError("Dung lượng ảnh bìa tối đa 2 MB.")

    original_name = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(original_name)
    random_filename = f"{uuid.uuid4().hex}{ext.lower()}"
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], random_filename))
    return random_filename


def delete_cover_image(filename):
    if not filename:
        return
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(file_path):
        os.remove(file_path)


def _is_safe_redirect(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (
        test_url.scheme in ("", "http", "https")
        and (test_url.netloc == "" or test_url.netloc == ref_url.netloc)
        and target.startswith("/")
        and not target.startswith("//")
    )


@app.template_filter("vnd")
def format_vnd(value):
    if value is None:
        return "0 đ"
    return f"{int(value):,}".replace(",", ".") + " đ"


@app.context_processor
def inject_global_counts():
    pending_count = (
        db.session.query(func.count(Order.id))
        .filter(Order.status == Order.STATUS_PENDING)
        .scalar()
        or 0
    )
    return {
        "cart_count": get_cart_total_quantity(),
        "pending_orders_count": pending_count,
    }


# PHẦN A · TRANG BÁN HÀNG (MÀN HÌNH ① – ⑤)
@app.route("/")
def index():
    return redirect(url_for("books"))


# MÀN HÌNH ①: DANH SÁCH SÁCH (/books)
@app.route("/books")
def books():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category_id", type=int)

    query = Book.query
    if q:
        keyword = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(keyword), Book.author.ilike(keyword)))
    if category_id:
        query = query.filter(Book.category_id == category_id)

    book_list = query.order_by(Book.created_at.desc(), Book.id.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "shop/books.html",
        books=book_list,
        categories=categories,
        q=q,
        selected_category=category_id,
    )


# MÀN HÌNH ②: CHỌN SÁCH (/books/<id>)
@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    cart = get_raw_cart()
    in_cart = int(cart.get(str(book.id), 0))
    max_addable = max(0, book.stock - in_cart)

    return render_template(
        "shop/book_detail.html",
        book=book,
        in_cart=in_cart,
        max_addable=max_addable,
    )


# THÊM VÀO GIỎ HÀNG (POST + CSRF + PRG)
@app.route("/cart/add/<int:book_id>", methods=["POST"])
def add_to_cart(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    next_url = request.form.get("next")
    fallback_url = url_for("book_detail", book_id=book.id)
    redirect_target = next_url if _is_safe_redirect(next_url) else fallback_url

    quantity = request.form.get("quantity", type=int)
    cart = get_raw_cart()
    key = str(book.id)
    in_cart = int(cart.get(key, 0))
    max_addable = book.stock - in_cart

    if quantity is None or quantity < 1 or quantity > max_addable:
        if book.stock <= 0:
            flash(f'Sách "{book.title}" hiện đã hết hàng.', "danger")
        elif max_addable <= 0:
            flash(
                f'Bạn đã thêm tối đa số lượng tồn kho ({book.stock} cuốn) của "{book.title}" vào giỏ.',
                "warning",
            )
        else:
            flash(
                f"Số lượng không hợp lệ (chỉ có thể thêm từ 1 đến {max_addable} cuốn).",
                "danger",
            )
        return redirect(redirect_target)

    cart[key] = in_cart + quantity
    session["cart"] = cart
    session.modified = True

    flash(f'Đã thêm {quantity}× "{book.title}" vào giỏ hàng.', "success")
    return redirect(redirect_target)


# MÀN HÌNH ③: GIỎ HÀNG (/cart)
@app.route("/cart")
def cart():
    items, subtotal, shipping_fee, grand_total = get_cart_details()
    return render_template(
        "shop/cart.html",
        items=items,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        grand_total=grand_total,
    )


@app.route("/cart/update/<int:book_id>", methods=["POST"])
def update_cart(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    action = request.form.get("action")
    cart = get_raw_cart()
    key = str(book.id)

    if key not in cart:
        return redirect(url_for("cart"))

    current_qty = int(cart[key])

    if action == "inc":
        if current_qty + 1 <= book.stock:
            cart[key] = current_qty + 1
        else:
            flash(f'Sách "{book.title}" chỉ còn {book.stock} cuốn trong kho.', "warning")
    elif action == "dec":
        if current_qty - 1 <= 0:
            del cart[key]
            flash(f'Đã xoá "{book.title}" khỏi giỏ hàng.', "info")
        else:
            cart[key] = current_qty - 1

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:book_id>", methods=["POST"])
def remove_from_cart(book_id):
    cart = get_raw_cart()
    key = str(book_id)
    if key in cart:
        del cart[key]
        session["cart"] = cart
        session.modified = True
        flash("Đã xoá sách khỏi giỏ hàng.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    session.pop("cart", None)
    flash("Đã xoá toàn bộ giỏ hàng.", "info")
    return redirect(url_for("cart"))


# MÀN HÌNH ④: THÔNG TIN KHÁCH HÀNG (/checkout)
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, subtotal, shipping_fee, grand_total = get_cart_details()

    if not items:
        flash("Giỏ hàng của bạn đang trống. Vui lòng chọn sách trước khi đặt hàng.", "warning")
        return redirect(url_for("cart"))

    form = CheckoutForm()

    if form.validate_on_submit():
        insufficient_books = []
        for item in items:
            fresh_book = db.session.get(Book, item["book"].id)
            if not fresh_book or fresh_book.stock < item["quantity"]:
                avail = fresh_book.stock if fresh_book else 0
                insufficient_books.append(
                    f'"{item["book"].title}" (yêu cầu {item["quantity"]}, chỉ còn {avail})'
                )

        if insufficient_books:
            flash(
                "Không thể đặt hàng do sách không đủ tồn kho: "
                + ", ".join(insufficient_books)
                + ".",
                "danger",
            )
            return redirect(url_for("cart"))

        order = Order(
            customer_name=form.customer_name.data.strip(),
            customer_phone=form.customer_phone.data.strip(),
            customer_email=form.customer_email.data.strip() if form.customer_email.data else None,
            shipping_address=form.shipping_address.data.strip(),
            note=form.note.data.strip() if form.note.data else None,
            payment_method=form.payment_method.data,
            shipping_fee=shipping_fee,
            total_amount=grand_total,
            status=Order.STATUS_PENDING,
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            book = db.session.get(Book, item["book"].id)
            order_item = OrderItem(
                order_id=order.id,
                book_id=book.id,
                quantity=item["quantity"],
                unit_price=book.price,
            )
            book.stock -= item["quantity"]
            db.session.add(order_item)

        db.session.commit()

        session.pop("cart", None)
        flash("Đặt hàng thành công!", "success")
        return redirect(url_for("order_success", order_id=order.id))

    return render_template(
        "shop/checkout.html",
        form=form,
        items=items,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        grand_total=grand_total,
    )


# MÀN HÌNH ⑤: ĐẶT THÀNH CÔNG (/orders/<id>)
@app.route("/orders/<int:order_id>")
def order_success(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    return render_template("shop/order_success.html", order=order)


# PHẦN B · TRANG QUẢN TRỊ /admin (MÀN HÌNH ⑥ – ⑪)
# MÀN HÌNH ⑥: TỔNG QUAN (/admin)
@app.route("/admin")
def admin_dashboard():
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_books = db.session.query(func.count(Book.id)).scalar() or 0

    pending_orders = (
        db.session.query(func.count(Order.id))
        .filter(Order.status == Order.STATUS_PENDING)
        .scalar()
        or 0
    )

    monthly_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.status == Order.STATUS_COMPLETED,
            func.coalesce(Order.completed_at, Order.created_at) >= month_start,
        )
        .scalar()
        or 0
    )

    low_stock_count = (
        db.session.query(func.count(Book.id)).filter(Book.stock <= 5).scalar() or 0
    )

    latest_orders = (
        Order.query.order_by(Order.created_at.desc(), Order.id.desc()).limit(5).all()
    )

    low_stock_books = (
        Book.query.filter(Book.stock <= 5)
        .order_by(Book.stock.asc(), Book.title.asc())
        .all()
    )

    seven_days_ago = (now - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    completed_recent = Order.query.filter(
        Order.status == Order.STATUS_COMPLETED,
        func.coalesce(Order.completed_at, Order.created_at) >= seven_days_ago,
    ).all()

    daily_map = {}
    for i in range(7):
        d = (seven_days_ago + timedelta(days=i)).date()
        daily_map[d] = 0

    for order in completed_recent:
        dt = order.completed_at or order.created_at
        if dt.date() in daily_map:
            daily_map[dt.date()] += order.total_amount

    revenue_7_days = [
        {"date": d.strftime("%d/%m"), "amount": amt} for d, amt in daily_map.items()
    ]

    return render_template(
        "admin/dashboard.html",
        current_month=now.month,
        total_books=total_books,
        pending_orders=pending_orders,
        monthly_revenue=monthly_revenue,
        low_stock_count=low_stock_count,
        latest_orders=latest_orders,
        low_stock_books=low_stock_books,
        revenue_7_days=revenue_7_days,
    )


# MÀN HÌNH ⑦: QUẢN LÝ SÁCH (/admin/books)
@app.route("/admin/books")
def admin_books():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category_id", type=int)
    stock_filter = request.args.get("stock", "").strip()

    query = Book.query

    if q:
        keyword = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(keyword), Book.author.ilike(keyword)))

    if category_id:
        query = query.filter(Book.category_id == category_id)

    if stock_filter == "in_stock":
        query = query.filter(Book.stock > 0)
    elif stock_filter == "low_stock":
        query = query.filter(Book.stock > 0, Book.stock <= 5)
    elif stock_filter == "out_of_stock":
        query = query.filter(Book.stock == 0)

    pagination = query.order_by(Book.created_at.desc(), Book.id.desc()).paginate(
        page=page, per_page=5, error_out=False
    )
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "admin/books.html",
        pagination=pagination,
        books=pagination.items,
        categories=categories,
        q=q,
        selected_category=category_id,
        stock_filter=stock_filter,
    )


@app.route("/admin/books/<int:book_id>/delete", methods=["POST"])
def admin_book_delete(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    if not book.is_deletable:
        flash(
            f'Không thể xoá sách "{book.title}" vì đã có trong đơn hàng.',
            "danger",
        )
        return redirect(url_for("admin_books"))

    old_cover = book.cover_image
    db.session.delete(book)
    db.session.commit()
    delete_cover_image(old_cover)

    flash(f'Đã xoá sách "{book.title}".', "success")
    return redirect(url_for("admin_books"))


# MÀN HÌNH ⑧: THÊM VÀ SỬA SÁCH (/admin/books/new & /admin/books/<id>/edit)
def _populate_category_choices(form):
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]


@app.route("/admin/books/new", methods=["GET", "POST"])
def admin_book_create():
    form = BookForm()
    _populate_category_choices(form)

    if form.validate_on_submit():
        try:
            cover_filename = save_cover_image(form.cover_image.data)
        except ValueError as err:
            form.cover_image.errors.append(str(err))
            return render_template("admin/book_form.html", form=form, book=None)

        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            publisher=form.publisher.data.strip() if form.publisher.data else None,
            category_id=form.category_id.data,
            publish_year=form.publish_year.data,
            price=form.price.data,
            stock=form.stock.data,
            description=form.description.data.strip() if form.description.data else None,
            cover_image=cover_filename,
        )
        db.session.add(book)
        db.session.commit()

        flash(f'Đã thêm sách "{book.title}".', "success")
        return redirect(url_for("admin_books"))

    return render_template("admin/book_form.html", form=form, book=None)


@app.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
def admin_book_edit(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    form = BookForm(book_id=book.id, obj=book)
    _populate_category_choices(form)

    if form.validate_on_submit():
        new_cover = None
        if form.cover_image.data and form.cover_image.data.filename:
            try:
                new_cover = save_cover_image(form.cover_image.data)
            except ValueError as err:
                form.cover_image.errors.append(str(err))
                return render_template("admin/book_form.html", form=form, book=book)

        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.publisher = form.publisher.data.strip() if form.publisher.data else None
        book.category_id = form.category_id.data
        book.publish_year = form.publish_year.data
        book.price = form.price.data
        book.stock = form.stock.data
        book.description = form.description.data.strip() if form.description.data else None

        if new_cover:
            old_cover = book.cover_image
            book.cover_image = new_cover
            delete_cover_image(old_cover)

        db.session.commit()

        flash(f'Đã cập nhật sách "{book.title}".', "success")
        return redirect(url_for("admin_books"))

    return render_template("admin/book_form.html", form=form, book=book)


# MÀN HÌNH ⑨: DANH MỤC SÁCH (/admin/categories)
def _get_categories_with_counts():
    return (
        db.session.query(Category, func.count(Book.id).label("book_count"))
        .outerjoin(Book, Category.id == Book.category_id)
        .group_by(Category.id)
        .order_by(Category.id.asc())
        .all()
    )


@app.route("/admin/categories", methods=["GET", "POST"])
def admin_categories():
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
        )
        db.session.add(category)
        db.session.commit()

        flash(f'Đã thêm danh mục "{category.name}".', "success")
        return redirect(url_for("admin_categories"))

    return render_template(
        "admin/categories.html",
        categories_with_counts=_get_categories_with_counts(),
        form=form,
        edit_category=None,
    )


@app.route("/admin/categories/<int:category_id>/edit", methods=["GET", "POST"])
def admin_category_edit(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)

    form = CategoryForm(category_id=category.id, obj=category)
    form.submit.label.text = "Lưu thay đổi"

    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.description = (
            form.description.data.strip() if form.description.data else None
        )
        db.session.commit()

        flash(f'Đã cập nhật danh mục "{category.name}".', "success")
        return redirect(url_for("admin_categories"))

    return render_template(
        "admin/categories.html",
        categories_with_counts=_get_categories_with_counts(),
        form=form,
        edit_category=category,
    )


@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
def admin_category_delete(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)

    book_count = category.books.count()
    if book_count > 0:
        flash(
            f'Không thể xoá "{category.name}": còn {book_count} sách.',
            "danger",
        )
        return redirect(url_for("admin_categories"))

    db.session.delete(category)
    db.session.commit()
    flash(f'Đã xoá danh mục "{category.name}".', "success")
    return redirect(url_for("admin_categories"))


# MÀN HÌNH ⑩: DANH SÁCH ĐƠN HÀNG (/admin/orders)
@app.route("/admin/orders")
def admin_orders():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()

    grouped = (
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    status_counts = dict(grouped)
    total_all = sum(status_counts.values())

    query = Order.query
    valid_statuses = [
        Order.STATUS_PENDING,
        Order.STATUS_SHIPPING,
        Order.STATUS_COMPLETED,
        Order.STATUS_CANCELLED,
    ]
    if status in valid_statuses:
        query = query.filter(Order.status == status)

    if q:
        keyword = f"%{q}%"
        conditions = [
            Order.customer_name.ilike(keyword),
            Order.customer_phone.ilike(keyword),
        ]
        raw_id = q.lstrip("#")
        if raw_id.isdigit():
            conditions.append(Order.id == int(raw_id))
        query = query.filter(or_(*conditions))

    filtered_count = query.count()
    filtered_total_amount = (
        query.with_entities(func.coalesce(func.sum(Order.total_amount), 0)).scalar()
        or 0
    )

    pagination = query.order_by(Order.created_at.desc(), Order.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        "admin/orders.html",
        pagination=pagination,
        orders=pagination.items,
        status=status,
        q=q,
        status_counts=status_counts,
        total_all=total_all,
        filtered_count=filtered_count,
        filtered_total_amount=filtered_total_amount,
    )


# MÀN HÌNH ⑪: CHI TIẾT ĐƠN HÀNG (/admin/orders/<id>)
@app.route("/admin/orders/<int:order_id>")
def admin_order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    return render_template("admin/order_detail.html", order=order)


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def admin_order_update_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    new_status = request.form.get("status", "").strip()

    if order.is_final_status or new_status not in order.allowed_next_statuses:
        flash("Thao tác chuyển trạng thái đơn hàng không hợp lệ.", "danger")
        return redirect(url_for("admin_order_detail", order_id=order.id))

    now = datetime.now()
    order.status = new_status

    if new_status == Order.STATUS_SHIPPING:
        order.shipped_at = now
    elif new_status == Order.STATUS_COMPLETED:
        order.completed_at = now
    elif new_status == Order.STATUS_CANCELLED:
        order.cancelled_at = now
        for item in order.items:
            if item.book:
                item.book.stock += item.quantity

    db.session.commit()
    flash(f'Đã cập nhật trạng thái đơn #{order.id} sang "{new_status}".', "success")
    return redirect(url_for("admin_order_detail", order_id=order.id))


if __name__ == "__main__":
    app.run(debug=True)