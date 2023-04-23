from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from sqlalchemy_serializer import SerializerMixin
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from werkzeug.utils import secure_filename
import stripe
import os

# This is your test secret API key.
stripe.api_key = 'sk_test_51LmeJSItRaWG2oZPktUAlpZ6ZnUzdsq9oZ2pjWOJcfH2KNIl2TwDgy1PmCy7r3VqwfEAaV9RDspOjLLRwAjq1aqF00c1B6Hf5z'
secret_key = 'SD1!id+_pK2$'
YOUR_DOMAIN = 'http://localhost:5000'


app = Flask(__name__)
app.secret_key = 'cs'
app.config['UPLOAD_FOLDER'] = 'finished-projects/81-100. [PRO]/96. [Web Development] An Online Shop/static/'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///items.db"
Bootstrap(app)
db = SQLAlchemy(app)


class Item(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(250))
    price_id = db.Column(db.String(250))
    name = db.Column(db.String(250), unique=True, nullable=False)
    on_sale = db.Column(db.String(250))
    old_price = db.Column(db.String(250))
    new_price = db.Column(db.String(250), nullable=False)
    file_name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)


db.create_all()


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': request.args.get('price_id'),
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


@app.route("/add", methods=["GET", "POST"])
def post_new_item():
    if request.args.get('key') != secret_key:
        return redirect(url_for('home'))

    if request.method == "POST":
        image = request.files['image']
        if image.filename != '':
            img = request.files['image']
            file_name = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            img.save(path)

            # adding item to stripe
            product = stripe.Product.create(name=request.form.get('name'))
            product_price = stripe.Price.create(
                product=product['id'], unit_amount=request.form.get('new_price'), currency="usd")

            # adding item to db
            new_item = Item(
                product_id=product['id'],
                price_id=product_price['id'],
                name=request.form.get('name'),
                on_sale=request.form.get('on_sale'),
                old_price=request.form.get('old_price'),
                new_price=request.form.get('new_price'),
                file_name=file_name,
                description=request.form.get('description')
            )
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('add.html')


@app.route('/buy/<id>')
def buy(id):
    item = Item.query.get(id)
    print(item.name)
    return render_template("shop-item.html", item=item)


@app.route('/edit', methods=['GET', 'POST'])
def edit_item():
    item = Item.query.get(request.args.get('id'))
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.on_sale = request.form.get('on_sale')
        item.old_price = request.form.get('old_price')
        item.new_price = request.form.get('new_price')
        item.description = request.form.get('description')
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html', item=item)


@app.route('/delete', methods=['GET', 'POST'])
def delete_item():
    item_to_delete = Item.query.get(request.args.get('id'))
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/')
def home():
    items = db.session.query(Item).all()
    return render_template("index.html", items=items)


@app.route("/contact", methods=['POST'])
def contact():
    if request.method == "POST":
        message = Mail(
            from_email='tairko2007@gmail.com',
            to_emails='tairko2007@gmail.com',
            subject='New Message',
            html_content=f'Name: { request.form.get("name") } | Email: {request.form.get("email") } | Phone: {request.form.get("phone_number") } | Message: «{request.form.get("message")}»'
        )
        try:
            sg = SendGridAPIClient(
                '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')
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
