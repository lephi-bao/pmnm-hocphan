from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    books = db.relationship("Book", back_populates="category", lazy="dynamic")

    @property
    def is_deletable(self):
        return self.books.count() == 0


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150), nullable=True)
    publish_year = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    category = db.relationship("Category", back_populates="books")
    order_items = db.relationship("OrderItem", back_populates="book", lazy="dynamic")

    @property
    def is_deletable(self):
        return self.order_items.count() == 0


class Order(db.Model):
    __tablename__ = "orders"

    STATUS_PENDING = "Chờ xác nhận"
    STATUS_SHIPPING = "Đang giao"
    STATUS_COMPLETED = "Hoàn tất"
    STATUS_CANCELLED = "Đã huỷ"

    VALID_TRANSITIONS = {
        STATUS_PENDING: [STATUS_SHIPPING, STATUS_CANCELLED],
        STATUS_SHIPPING: [STATUS_COMPLETED, STATUS_CANCELLED],
        STATUS_COMPLETED: [],
        STATUS_CANCELLED: [],
    }

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    customer_email = db.Column(db.String(120), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(50), nullable=False, default="Tiền mặt khi nhận hàng")

    shipping_fee = db.Column(db.Integer, nullable=False, default=20000)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)

    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    shipped_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="select"
    )

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items)

    @property
    def allowed_next_statuses(self):
        return self.VALID_TRANSITIONS.get(self.status, [])

    @property
    def is_final_status(self):
        return self.status in (self.STATUS_COMPLETED, self.STATUS_CANCELLED)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    book = db.relationship("Book", back_populates="order_items")

    @property
    def line_total(self):
        return self.quantity * self.unit_price