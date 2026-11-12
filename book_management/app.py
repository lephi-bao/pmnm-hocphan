import click
from flask import Flask, abort, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from models import db, Category, Book

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-chi-dung-khi-phattrien"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///book_management.db"

# Gắn db vào app và tạo bảng
db.init_app(app)
with app.app_context():
    db.create_all()


@app.cli.command("seed-data")
def seed_data():
    """Lệnh tạo dữ liệu mẫu tự động qua Terminal"""
    if db.session.scalar(db.select(func.count(Category.id))) > 0:
        click.echo("Dữ liệu đã tồn tại, không cần seed thêm.")
        return

    # 1. Tạo 5 danh mục
    cat1 = Category(name="Lập trình", description="Sách về công nghệ, lập trình.")
    cat2 = Category(name="Văn học", description="Tiểu thuyết, truyện ngắn, thơ.")
    cat3 = Category(name="Kinh tế", description="Sách kinh doanh, tài chính, đầu tư.")
    cat4 = Category(name="Tâm lý học", description="Kiến thức tâm lý, phát triển bản thân.")
    cat5 = Category(name="Khoa học", description="Khoa học tự nhiên, vật lý, vũ trụ.")
    
    db.session.add_all([cat1, cat2, cat3, cat4, cat5])
    db.session.commit()

    # 2. Tạo 5 sách tương ứng với các danh mục trên
    book1 = Book(title="Flask Cơ Bản", author="Python Team", price=150000, quantity=10, publish_year=2023, category_id=cat1.id)
    book2 = Book(title="Nhà Giả Kim", author="Paulo Coelho", price=85000, quantity=5, publish_year=1988, category_id=cat2.id)
    book3 = Book(title="Cha Giàu Cha Nghèo", author="Robert Kiyosaki", price=120000, quantity=20, publish_year=1997, category_id=cat3.id)
    book4 = Book(title="Tư Duy Nhanh Và Chậm", author="Daniel Kahneman", price=195000, quantity=8, publish_year=2011, category_id=cat4.id)
    book5 = Book(title="Lược Sử Thời Gian", author="Stephen Hawking", price=115000, quantity=12, publish_year=1988, category_id=cat5.id)
    
    db.session.add_all([book1, book2, book3, book4, book5])
    db.session.commit()
    
    click.echo("Đã tạo dữ liệu mẫu thành công (5 danh mục, 5 sách)!")


@app.route("/")
def dashboard():
    cat_count = db.session.query(func.count(Category.id)).scalar()
    book_count = db.session.query(func.count(Book.id)).scalar()
    total_stock = db.session.query(func.coalesce(func.sum(Book.quantity), 0)).scalar()
    total_value = db.session.query(
        func.coalesce(func.sum(Book.price * Book.quantity), 0)).scalar()

    per_category = (
        db.session.query(Category.name, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(func.count(Book.id).desc())
        .all()
    )
    recent_books = Book.query.order_by(Book.id.desc()).limit(6).all()
    low_stock_books = (Book.query.filter(Book.quantity <= 5).order_by(Book.quantity.asc()).limit(6).all())

    return render_template(
        "dashboard.html",
        cat_count=cat_count, book_count=book_count,
        total_stock=total_stock, total_value=total_value,
        per_category=per_category, recent_books=recent_books,
        low_stock_books=low_stock_books,
    )


# DANH MỤC SÁCH
@app.route("/categories")
def categories():
    all_categories = db.session.execute(db.select(Category).order_by(Category.id.asc())).scalars().all()
    return render_template("categories/list.html", categories=all_categories)

@app.route("/categories/<int:id>")
def category_detail(id):
    cat = db.session.get(Category, id)
    if not cat:
        abort(404)
    return render_template("categories/detail.html", category=cat)

@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        if name:
            db.session.add(Category(name=name, description=description))
            db.session.commit()
            flash("Thêm danh mục mới thành công!", "success")
            return redirect(url_for("categories"))
            
    return render_template("categories/add.html")

@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
def edit_category(id):
    cat = db.session.get(Category, id)
    if not cat:
        return redirect(url_for("categories"))
        
    if request.method == "POST":
        cat.name = request.form.get("name")
        cat.description = request.form.get("description")
        db.session.commit()
        flash("Đã cập nhật danh mục thành công!", "success")
        return redirect(url_for("categories"))
        
    return render_template("categories/edit.html", category=cat)

@app.route("/categories/delete/<int:id>", methods=["POST"])
def delete_category(id):
    cat = db.session.get(Category, id)
    if cat:
        db.session.delete(cat)
        db.session.commit()
    return redirect(url_for("categories"))

# SÁCH
@app.route("/books")
def books():
    all_books = db.session.execute(db.select(Book).order_by(Book.id.asc())).scalars().all()
    return render_template("books/list.html", books=all_books)

@app.route("/books/<int:id>")
def book_detail(id):
    book = db.session.get(Book, id)
    if not book:
        abort(404)
    return render_template("books/detail.html", book=book)

@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        price = request.form.get("price", type=float)
        quantity = request.form.get("quantity", type=int)
        publish_year = request.form.get("publish_year", type=int)
        description = request.form.get("description")
        category_id = request.form.get("category_id", type=int)
        
        if title and author and price is not None and quantity is not None and category_id:
            db.session.add(Book(
                title=title, author=author, price=price, quantity=quantity, 
                publish_year=publish_year, description=description, category_id=category_id
            ))
            db.session.commit()
            flash("Thêm sách mới thành công!", "success")
            return redirect(url_for("books"))
            
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template("books/add.html", categories=categories)

@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    book = db.session.get(Book, id)
    if not book:
        return redirect(url_for("books"))
        
    if request.method == "POST":
        book.title = request.form.get("title")
        book.author = request.form.get("author")
        book.price = request.form.get("price", type=float)
        book.quantity = request.form.get("quantity", type=int)
        book.publish_year = request.form.get("publish_year", type=int)
        book.description = request.form.get("description")
        book.category_id = request.form.get("category_id", type=int)
        
        db.session.commit()
        flash("Đã cập nhật thông tin sách thành công!", "success")
        return redirect(url_for("books"))
        
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template("books/edit.html", book=book, categories=categories)

@app.route("/books/delete/<int:id>", methods=["POST"])
def delete_book(id):
    book = db.session.get(Book, id)
    if book:
        db.session.delete(book)
        db.session.commit()
    return redirect(url_for("books"))

# Xử lý lỗi 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404