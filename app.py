from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():

    a = request.form.get('a')
    b = request.form.get('b')
    num_a = 0
    num_b = 0

    if a is None:
        num_a = 0
    else:
        num_a = float(a)
    if b is None:
        num_b = 0
    else:
        num_b = float(b)

    div = 'Không thể chia'
    if num_b != 0:
        div = num_a / num_b

    ketQua = {
        'cong': num_a + num_b,
        'tru': num_a - num_b,
        'nhan': num_a * num_b,
        'chia': div
    }
    return render_template(
        'math.html',
        a=a,
        b=b,
        ketQua = ketQua
    )

if __name__ == '__main__':
    app.run(debug=True)