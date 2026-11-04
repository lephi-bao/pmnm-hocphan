from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func

TEXT = {"Content-Type": "text/plain; charset=utf-8"}

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SECRET_KEY'] = "dev-chi-dung-khi-phat-trien"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qlsv.db'
db.init_app(app)

class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self) -> str:
        return f"<Student {self.mssv} - {self.name}>"

with app.app_context():
    db.create_all()

@app.route('/them-mau')
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm mẫu nữa."
    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=8.5)
    before = an.id
    db.session.add(an)
    db.session.add_all([
        Student(mssv="23T1020002", name="Nguyễn Văn Bình", gpa=7.5),
        Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=6.5),
        Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=9.5),
        Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=5.5),
    ])
    db.session.commit()
    return (f"Đã thêm 5 sinh viên, id của An: "
            f"trước commit = {before}, "
            f"sau commit = {an.id}")

@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(db.select(func.count(Student.id))) == 0:
        return "Chưa có sinh viên nào, hãy truy cập /them-mau trước."
    lines = []
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")
    everyone = db.session.execute(db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")

    stmt = (
        db.select(Student)
        .where(Student.gpa >= 8)
        .order_by(Student.gpa.desc())
    )
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")

    binh = db.session.scalar(
        db.select(Student).filter_by(mssv="23T1020002")
    )
    lines.append(f"5. MSSV 23T1020002: {binh}")

    count = db.session.scalar(db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")
    return "\n".join(lines), TEXT

@app.get("/danh-sach")
def list_students():
    ds = db.session.execute(db.select(Student)).scalars().all()
    return render_template("list_student.html", ds_sinh_vien=ds)

if __name__ == "__main__":
    app.run(debug=True)