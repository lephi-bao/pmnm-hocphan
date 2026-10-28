from datetime import datetime
from flask import Flask, render_template, request, abort
import math

app = Flask(__name__)

SHOP = {
    "name": "cà phê Sông Hương",
    "address": "12 Lê Lợi, Huế",
    "open": 7,
    "close": 22,
}

PROMOTIONS = [
    "Giảm 10% cho sinh viên",
    "Mua 2 tặng 1 vào thứ Hai",
]

MENU = [
    {"id": 1, "name": "cà phê đen", "price": 20000, "available": True, "image": "ca-phe-den.jpg"},
    {"id": 2, "name": "bạc xỉu", "price": 30000, "available": True, "image": "bac-xiu.jpg"},
    {"id": 3, "name": "cà phê sữa", "price": 25000, "available": True, "image": "ca-phe-sua.jpg"},
    {"id": 4, "name": "trà đào", "price": 35000, "available": True, "image": "tra-dao.jpg"},
    {"id": 5, "name": "trà vải", "price": 35000, "available": True, "image": "tra-vai.jpg"},
    {"id": 6, "name": "bánh mì", "price": 15000, "available": False, "image": "banh-mi.jpg"},
    {"id": 7, "name": "bánh ngọt", "price": 20000, "available": True, "image": "banh-ngot.jpg"}
]

@app.get("/")
def index():
    hour = request.args.get("gio", type=int)
    if hour is None:
        hour = datetime.now().hour

    is_open = SHOP["open"] <= hour < SHOP["close"]

    return render_template(
        "index.html",
        shop=SHOP,
        hour=hour,
        is_open=is_open,
        promotions=PROMOTIONS,
    )

@app.template_filter('vnd')
def format_vnd(value):
    return f"{value:,.0f}".replace(",", ".") + " đ"

@app.route('/menu')
def menu():
    page_param = request.args.get('page', 1)
    
    # 1. Ép kiểu tham số page, nếu gửi 'abc' thì mặc định về 1
    try:
        page = int(page_param)
    except (ValueError, TypeError):
        page = 1

    per_page = 3  
    total_items = len(MENU)
    pages = math.ceil(total_items / per_page)

    if page < 1 or (pages > 0 and page > pages):
        abort(404)

    start = (page - 1) * per_page
    end = start + per_page
    items = MENU[start:end]

    # TRUYỀN ĐỦ CÁC BIẾN items, page, pages SANG TEMPLATE
    return render_template('menu.html', items=items, page=page, pages=pages)

@app.route('/contact')
def contact():
    return render_template('contact.html', shop=SHOP)

# Route Bài 1: Máy tính cơ bản
@app.route('/bai-01', methods=['GET', 'POST'])
def bai_01():
    a_raw = ''
    b_raw = ''
    op = '+'
    err_a = None
    err_b = None
    err_op = None
    result = None

    if request.method == 'POST':
        a_raw = request.form.get('a', '').strip()
        b_raw = request.form.get('b', '').strip()
        op = request.form.get('op', '+')

        # Validate a
        val_a = None
        if not a_raw:
            err_a = "Vui lòng nhập số a"
        else:
            try:
                val_a = float(a_raw.replace(',', '.'))
            except ValueError:
                err_a = "Số thứ nhất không hợp lệ"

        # Validate b
        val_b = None
        if not b_raw:
            err_b = "Vui lòng nhập số b"
        else:
            try:
                val_b = float(b_raw.replace(',', '.'))
            except ValueError:
                err_b = "Số thứ hai không hợp lệ"

        # Validate op
        if op not in ['+', '-', '*', '/']:
            err_op = "Phép toán không hợp lệ"

        # Tính toán
        if not err_a and not err_b and not err_op:
            res_val = None
            if op == '+':
                res_val = val_a + val_b
            elif op == '-':
                res_val = val_a - val_b
            elif op == '*':
                res_val = val_a * val_b
            elif op == '/':
                if val_b == 0:
                    err_b = "Không thể chia cho 0"
                else:
                    res_val = val_a / val_b

            if not err_b and res_val is not None:
                fmt_a = int(val_a) if val_a.is_integer() else val_a
                fmt_b = int(val_b) if val_b.is_integer() else val_b
                fmt_res = int(res_val) if isinstance(res_val, float) and res_val.is_integer() else round(res_val, 4)
                result = f"{fmt_a} {op} {fmt_b} = {fmt_res}"

    return render_template(
        'bai_01.html',
        a_raw=a_raw,
        b_raw=b_raw,
        op=op,
        err_a=err_a,
        err_b=err_b,
        err_op=err_op,
        result=result
    )

# --- BÀI 02 - TÍNH ĐIỂM HỌC PHẦN ---
@app.route('/bai-02', methods=['GET', 'POST'])
@app.route('/diem-hoc-phan', methods=['GET', 'POST'])
def bai_02():
    dcc_raw = ''
    dgk_raw = ''
    dck_raw = ''
    err_dcc = None
    err_dgk = None
    err_dck = None
    result_text = None
    sub_text = None
    alert_class = None

    if request.method == 'POST':
        dcc_raw = request.form.get('dcc', '').strip()
        dgk_raw = request.form.get('dgk', '').strip()
        dck_raw = request.form.get('dck', '').strip()

        val_dcc = None
        val_dgk = None
        val_dck = None

        # 1. Kiểm tra Điểm chuyên cần
        if not dcc_raw:
            err_dcc = "Vui lòng nhập điểm chuyên cần"
        else:
            try:
                val_dcc = float(dcc_raw.replace(',', '.'))
                if not (0 <= val_dcc <= 10):
                    err_dcc = "Điểm phải từ 0 đến 10"
            except ValueError:
                err_dcc = "Điểm không hợp lệ"

        # 2. Kiểm tra Điểm giữa kỳ
        if not dgk_raw:
            err_dgk = "Vui lòng nhập điểm giữa kỳ"
        else:
            try:
                val_dgk = float(dgk_raw.replace(',', '.'))
                if not (0 <= val_dgk <= 10):
                    err_dgk = "Điểm phải từ 0 đến 10"
            except ValueError:
                err_dgk = "Điểm không hợp lệ"

        # 3. Kiểm tra Điểm cuối kỳ
        if not dck_raw:
            err_dck = "Vui lòng nhập điểm cuối kỳ"
        else:
            try:
                val_dck = float(dck_raw.replace(',', '.'))
                if not (0 <= val_dck <= 10):
                    err_dck = "Điểm phải từ 0 đến 10"
            except ValueError:
                err_dck = "Điểm không hợp lệ"

        # 4. Tính toán nếu dữ liệu hợp lệ
        if not err_dcc and not err_dgk and not err_dck:
            # Điều kiện điểm liệt: Cuối kỳ dưới 1.0
            if val_dck < 1.0:
                result_text = "Điểm tổng kết: 0.0 (F)"
                sub_text = "Bị điểm liệt cuối kỳ (dưới 1.0)"
                alert_class = "alert-danger"
            else:
                score = round(val_dcc * 0.1 + val_dgk * 0.3 + val_dck * 0.6, 1)

                if score >= 8.5:
                    grade, gpa = 'A', 4.0
                    alert_class = "alert-success"
                elif score >= 7.0:
                    grade, gpa = 'B', 3.0
                    alert_class = "alert-success"
                elif score >= 5.5:
                    grade, gpa = 'C', 2.0
                    alert_class = "alert-info"
                elif score >= 4.0:
                    grade, gpa = 'D', 1.0
                    alert_class = "alert-warning"
                else:
                    grade, gpa = 'F', 0.0
                    alert_class = "alert-danger"

                fmt_score = int(score) if score.is_integer() else score
                result_text = f"Điểm tổng kết: {fmt_score} - Điểm chữ: {grade}"
                sub_text = f"Điểm hệ 4: {gpa}"

    return render_template(
        'bai_02.html',  # Gọi chính xác tệp templates/bai_02.html
        dcc_raw=dcc_raw,
        dgk_raw=dgk_raw,
        dck_raw=dck_raw,
        err_dcc=err_dcc,
        err_dgk=err_dgk,
        err_dck=err_dck,
        result_text=result_text,
        sub_text=sub_text,
        alert_class=alert_class
    )

# --- BÀI 03 - TÍNH CHỈ SỐ BMI ---
@app.route('/bai-03', methods=['GET', 'POST'])
def bai_03():
    height_raw = ''
    weight_raw = ''
    err_height = None
    err_weight = None
    bmi_value = None
    category = None
    alert_class = None
    ideal_weight = None

    if request.method == 'POST':
        height_raw = request.form.get('height', '').strip()
        weight_raw = request.form.get('weight', '').strip()

        val_h = None
        val_w = None

        # 1. Kiểm tra Chiều cao (cm)
        if not height_raw:
            err_height = "Vui lòng nhập chiều cao."
        else:
            try:
                val_h = float(height_raw.replace(',', '.'))
                if val_h < 50 or val_h > 250:
                    if 0.5 <= val_h <= 2.5:
                        err_height = "Giá trị phải từ 50 đến 250. (nhập mét thay vì cm)"
                    else:
                        err_height = "Giá trị phải từ 50 đến 250."
            except ValueError:
                err_height = "Vui lòng nhập một số."

        # 2. Kiểm tra Cân nặng (kg)
        if not weight_raw:
            err_weight = "Vui lòng nhập cân nặng."
        else:
            try:
                val_w = float(weight_raw.replace(',', '.'))
                if val_w < 10 or val_w > 300:
                    err_weight = "Giá trị phải từ 10 đến 300."
            except ValueError:
                err_weight = "Vui lòng nhập một số."

        # 3. Tính toán BMI nếu dữ liệu hợp lệ
        if not err_height and not err_weight and val_h and val_w:
            h_m = val_h / 100.0  # Đổi cm sang mét
            bmi = round(val_w / (h_m ** 2), 1)
            bmi_value = f"{bmi}"

            # Phân loại theo chuẩn Châu Á
            if bmi < 18.5:
                category = "Thiếu cân"
                alert_class = "alert-warning"  # Màu vàng
            elif bmi < 23.0:
                category = "Bình thường"
                alert_class = "alert-success"  # Màu xanh
            elif bmi < 25.0:
                category = "Thừa cân"
                alert_class = "alert-warning"  # Màu vàng
            else:
                category = "Béo phì"
                alert_class = "alert-danger"   # Màu đỏ

            # Tính cân nặng nên có dựa trên BMI 18.5 - 22.9
            min_w = round(18.5 * (h_m ** 2), 1)
            max_w = round(22.9 * (h_m ** 2), 1)
            
            # Định dạng bỏ đuôi .0 nếu là số nguyên
            fmt_min = int(min_w) if min_w.is_integer() else min_w
            fmt_max = int(max_w) if max_w.is_integer() else max_w
            ideal_weight = f"nên có {fmt_min} – {fmt_max} kg"

    return render_template(
        'bai_03.html',
        height_raw=height_raw,
        weight_raw=weight_raw,
        err_height=err_height,
        err_weight=err_weight,
        bmi_value=bmi_value,
        category=category,
        alert_class=alert_class,
        ideal_weight=ideal_weight
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)