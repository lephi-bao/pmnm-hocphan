from app import app
from models import Book, Category, db


def seed():
    with app.app_context():
        if Category.query.count() > 0:
            print("Dữ liệu mẫu đã tồn tại.")
            return

        c_prog = Category(name="Lập trình", description="Sách lập trình ứng dụng và web")
        c_db = Category(name="Cơ sở dữ liệu", description="Thiết kế và quản trị CSDL")
        c_tool = Category(name="Công cụ", description="Quản lý mã nguồn và công cụ")
        c_net = Category(name="Mạng", description="Mạng máy tính và truyền thông")
        c_skill = Category(name="Kỹ năng lập trình", description="Tư duy và thực hành mã sạch")
        c_design = Category(name="Thiết kế", description="Thiết kế giao diện và trải nghiệm")
        db.session.add_all([c_prog, c_db, c_tool, c_net, c_skill, c_design])
        db.session.flush()

        books = [
            Book(
                title="Clean Code",
                author="Robert C. Martin",
                publisher="Prentice Hall",
                publish_year=2008,
                price=180000,
                stock=5,
                category_id=c_skill.id,
                description="Cẩm nang viết mã sạch và tái cấu trúc mã nguồn.",
            ),
            Book(
                title="Mạng máy tính",
                author="Lê Văn C",
                publisher="NXB Giáo dục",
                publish_year=2023,
                price=110000,
                stock=12,
                category_id=c_net.id,
                description="Kiến trúc phân tầng TCP/IP, định tuyến và giao thức mạng.",
            ),
            Book(
                title="Pro Git",
                author="Scott Chacon",
                publisher="Apress",
                publish_year=2014,
                price=150000,
                stock=14,
                category_id=c_tool.id,
                description="Hướng dẫn sử dụng Git từ cơ bản đến nâng cao.",
            ),
            Book(
                title="Cơ sở dữ liệu",
                author="Trần Văn B",
                publisher="NXB Đại học Huế",
                publish_year=2022,
                price=85000,
                stock=0,
                category_id=c_db.id,
                description="Mô hình quan hệ, chuẩn hoá dữ liệu và ngôn ngữ SQL.",
            ),
            Book(
                title="Giáo trình Flask",
                author="Miguel Grinberg",
                publisher="O'Reilly",
                publish_year=2024,
                price=120000,
                stock=19,
                category_id=c_prog.id,
                description="Phát triển ứng dụng web với Flask, Jinja2, SQLAlchemy và Flask-WTF.",
            ),
            Book(
                title="Lập trình Python cơ bản",
                author="Nguyễn Văn A",
                publisher="NXB Đại học Huế",
                publish_year=2024,
                price=95000,
                stock=28,
                category_id=c_prog.id,
                description="Giáo trình nhập môn ngôn ngữ lập trình Python.",
            ),
        ]
        db.session.add_all(books)
        db.session.commit()
        print("Đã nạp dữ liệu mẫu thành công!")


if __name__ == "__main__":
    seed()