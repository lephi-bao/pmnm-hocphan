from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from sqlalchemy import func
from wtforms import (
    IntegerField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)
from models import Book, Category


class CheckoutForm(FlaskForm):
    customer_name = StringField(
        "Họ tên",
        validators=[
            DataRequired(message="Vui lòng nhập họ tên."),
            Length(max=120, message="Họ tên tối đa 120 ký tự."),
        ],
    )
    customer_phone = StringField(
        "Số điện thoại",
        validators=[
            DataRequired(message="Vui lòng nhập số điện thoại."),
            Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."),
        ],
    )
    customer_email = StringField(
        "Email",
        validators=[
            Optional(),
            Email(message="Email không đúng định dạng."),
            Length(max=120),
        ],
    )
    shipping_address = TextAreaField(
        "Địa chỉ giao hàng",
        validators=[DataRequired(message="Vui lòng nhập địa chỉ giao hàng.")],
    )
    note = TextAreaField("Ghi chú", validators=[Optional()])
    payment_method = RadioField(
        "Thanh toán",
        choices=[
            ("Tiền mặt khi nhận hàng", "Tiền mặt khi nhận hàng"),
            ("Chuyển khoản", "Chuyển khoản"),
        ],
        default="Tiền mặt khi nhận hàng",
        validators=[DataRequired(message="Vui lòng chọn phương thức thanh toán.")],
    )
    submit = SubmitField("Xác nhận đặt hàng")


class BookForm(FlaskForm):
    title = StringField(
        "Tên sách",
        validators=[
            DataRequired(message="Vui lòng nhập tên sách."),
            Length(max=200, message="Tên sách tối đa 200 ký tự."),
        ],
    )
    author = StringField(
        "Tác giả",
        validators=[
            DataRequired(message="Vui lòng nhập tên tác giả."),
            Length(max=150, message="Tên tác giả tối đa 150 ký tự."),
        ],
    )
    publisher = StringField(
        "Nhà xuất bản",
        validators=[Optional(), Length(max=150)],
    )
    category_id = SelectField(
        "Danh mục",
        coerce=int,
        validators=[DataRequired(message="Vui lòng chọn danh mục.")],
    )
    publish_year = IntegerField("Năm xuất bản", validators=[Optional()])
    price = IntegerField(
        "Giá (đồng)",
        validators=[
            InputRequired(message="Vui lòng nhập giá bán."),
            NumberRange(min=1000, message="Giá bán phải từ 1.000 đ trở lên."),
        ],
    )
    stock = IntegerField(
        "Tồn kho",
        validators=[
            InputRequired(message="Vui lòng nhập số lượng tồn kho."),
            NumberRange(min=0, message="Tồn kho không âm."),
        ],
    )
    description = TextAreaField("Mô tả", validators=[Optional()])
    cover_image = FileField(
        "Ảnh bìa",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                message="Chỉ chấp nhận ảnh định dạng JPG, PNG hoặc WEBP.",
            ),
        ],
    )
    submit = SubmitField("Lưu")

    def __init__(self, book_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_id = book_id

    def validate_title(self, field):
        normalized = field.data.strip().lower()
        query = Book.query.filter(func.lower(Book.title) == normalized)
        if self.book_id is not None:
            query = query.filter(Book.id != self.book_id)
        if query.first():
            raise ValidationError("Tên sách đã tồn tại.")

    def validate_publish_year(self, field):
        if field.data is not None:
            current_year = datetime.now().year
            if field.data < 1900 or field.data > current_year:
                raise ValidationError(f"Năm xuất bản phải từ 1900 đến {current_year}.")


class CategoryForm(FlaskForm):
    name = StringField(
        "Tên",
        validators=[
            DataRequired(message="Vui lòng nhập tên danh mục."),
            Length(max=100, message="Tên danh mục tối đa 100 ký tự."),
        ],
    )
    description = TextAreaField("Mô tả", validators=[Optional()])
    submit = SubmitField("+ Thêm")

    def __init__(self, category_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id = category_id

    def validate_name(self, field):
        normalized = field.data.strip().lower()
        query = Category.query.filter(func.lower(Category.name) == normalized)
        if self.category_id is not None:
            query = query.filter(Category.id != self.category_id)
        if query.first():
            raise ValidationError("Danh mục đã tồn tại.")