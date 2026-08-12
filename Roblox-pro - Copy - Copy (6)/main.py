from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random


app = Flask(__name__)

app.secret_key = "robloxpro_secret"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)



class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50))

    email = db.Column(db.String(100), unique=True)

    roblox_username = db.Column(db.String(50))

    phone = db.Column(db.String(20))

    password = db.Column(db.String(100))


class Order(db.Model):
        
    id = db.Column(db.Integer, primary_key=True)

    customer_name = db.Column(db.String(100), nullable=False)

    roblox_username = db.Column(db.String(100), nullable=False)

    phone = db.Column(db.String(30), nullable=False)

    products = db.Column(db.Text, nullable=False)

    total_price = db.Column(db.Integer, nullable=False)


class RedeemClaim(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100))

    roblox_username = db.Column(db.String(100))

    phone = db.Column(db.String(30))

    code = db.Column(db.String(100))

    reward = db.Column(db.String(200))


class RedeemCode(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(100), unique=True)

    reward = db.Column(db.String(200))

    used_users = db.Column(db.Text, default="")



class DiscountCode(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(100), unique=True, nullable=False)

    amount = db.Column(db.Integer, nullable=False)

    used_users = db.Column(db.Text, default="")



class UserSpin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100))

    roblox_username = db.Column(db.String(100))

    phone = db.Column(db.String(30))

    spins = db.Column(db.Integer, default=0)

    last_daily_spin = db.Column(db.DateTime)



class SpinClaim(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100))

    roblox_username = db.Column(db.String(100))

    phone = db.Column(db.String(30))

    reward = db.Column(db.String(100))



class SpinReward(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    reward = db.Column(db.String(100))

    chance = db.Column(db.Float)



class Item(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    price = db.Column(db.Integer)

    category = db.Column(db.String(20))

    image = db.Column(db.String(300))






@app.route("/")
def home():

    spin = 0

    if "user" in session:

        check_daily_spin()

        user_spin = get_user_spin()

        if user_spin:
            spin = user_spin.spins


    return render_template(
        "index.html",
        spin=spin
    )



@app.route("/add_spin_reward", methods=["POST"])
def add_spin_reward():

    reward = request.form["reward"]
    chance = float(request.form["chance"])


    spin_reward = SpinReward(

        reward=reward,

        chance=chance

    )


    db.session.add(spin_reward)

    db.session.commit()


    return redirect("/admin")



@app.route("/delete_spin_reward/<int:id>")
def delete_spin_reward(id):

    reward = SpinReward.query.get(id)

    if reward:

        db.session.delete(reward)

        db.session.commit()


    return redirect("/admin")



@app.route("/delete_spin/<int:id>")
def delete_spin(id):

    spin = SpinClaim.query.get_or_404(id)

    db.session.delete(spin)

    db.session.commit()

    return redirect("/admin")



@app.route("/shop")
def shop():

    return render_template("shop.html")





@app.route("/seeds")
def seeds():

    items = Item.query.all()

    print(items)

    return render_template(
        "seeds.html",
        items=items
    )






# افزودن به سبد خرید
@app.route("/add_cart/<name>/<int:price>")
def add_cart(name, price):

    cart = session.get("cart", [])



    for item in cart:

        if item["name"] == name:

            item["count"] = item.get("count", 1) + 1

            session["cart"] = cart

            session.modified = True

            return redirect("/cart")




    cart.append({

        "name": name,

        "price": int(price),

        "count": 1

    })



    session["cart"] = cart

    session.modified = True



    return redirect("/cart")








# سبد خرید
@app.route("/cart")
def cart():
    items = session.get("cart", [])

    total = 0

    for item in items:
        item["price"] = int(item["price"])
        item["count"] = int(item.get("count", 1))

        total += item["price"] * item["count"]

    discount = session.get("discount", 0)

    if discount:
        total -= discount

        if total < 0:
            total = 0

    session["cart"] = items
    session.modified = True

    message = session.pop("discount_message", "")


    return render_template(
        "cart.html",
        items=items,
        total=total,
        discount_message=message
)








# زیاد کردن تعداد
@app.route("/plus/<name>")
def plus(name):

    cart = session.get("cart", [])



    for item in cart:

        if item["name"] == name:

            item["count"] += 1



    session["cart"] = cart

    session.modified = True


    return redirect("/cart")








# کم کردن تعداد
@app.route("/minus/<name>")
def minus(name):

    cart = session.get("cart", [])



    for item in cart:

        if item["name"] == name:

            item["count"] -= 1



            if item["count"] <= 0:

                cart.remove(item)



            break



    session["cart"] = cart

    session.modified = True


    return redirect("/cart")








# حذف محصول
@app.route("/remove/<name>")
def remove(name):

    cart = session.get("cart", [])


    for item in cart:

        if item["name"] == name:

            cart.remove(item)

            break


    session["cart"] = cart

    session.modified = True


    return redirect("/cart")



@app.route("/spin_now", methods=["POST"])
def spin_now():

    if "user" not in session:
        return redirect("/login")

    user_spin = get_user_spin()

    if user_spin.spins <= 0:
        session["spin_message"] = "❌ شما اسپین ندارید"
        return redirect("/spin")

    # کم کردن یک اسپین
    user_spin.spins -= 1

    rewards = SpinReward.query.all()

    if not rewards:
        session["spin_message"] = "❌ هیچ جایزه‌ای وجود ندارد"
        return redirect("/spin")

    # انتخاب جایزه
    reward = random.choice(rewards)

    # ثبت درخواست جایزه
    claim = SpinClaim(
        username=session["user"],
        roblox_username=session["roblox_username"],
        phone=session["phone"],
        reward=reward.reward
    )

    db.session.add(claim)
    db.session.commit()

    # پیام برای نمایش در صفحه
    session["spin_message"] = f"🎉 شما برنده شدید: {reward.reward}"

    return redirect("/spin")


@app.route("/add_spin", methods=["POST"])
def add_spin():

    roblox_username = request.form["roblox_username"]
    amount = int(request.form["amount"])


    user_spin = UserSpin.query.filter_by(
        roblox_username=roblox_username
    ).first()


    if user_spin:

        user_spin.spins += amount


    else:

        user_spin = UserSpin(

            roblox_username=roblox_username,

            spins=amount

        )

        db.session.add(user_spin)


    db.session.commit()


    return redirect("/admin")




    db.session.add(claim)

    db.session.commit()


    session["last_reward"] = reward.reward


    return redirect("/spin")



@app.route("/remove_spin", methods=["POST"])
def remove_spin():

    roblox_username = request.form["roblox_username"]
    amount = int(request.form["amount"])


    user_spin = UserSpin.query.filter_by(
        roblox_username=roblox_username
    ).first()


    if user_spin:

        user_spin.spins -= amount

        if user_spin.spins < 0:
            user_spin.spins = 0


        db.session.commit()


    return redirect("/admin")


@app.route("/add_item", methods=["POST"])
def add_item():

    name = request.form["name"]
    price = int(request.form["price"])
    category = request.form["category"]
    image = request.form["image"]


    item = Item(
        name=name,
        price=price,
        category=category,
        image=image
    )


    db.session.add(item)
    db.session.commit()


    return redirect("/admin")



# رفتن به صفحه پرداخت
@app.route("/checkout")
def checkout():

    if "user" not in session:
        return redirect("/login")


    cart = session.get("cart", [])


    if not cart:
        return redirect("/cart")


    products = ""

    total = 0


    for item in cart:

        products += f'{item["name"]} × {item["count"]}\n'

        total += int(item["price"]) * int(item["count"])



    # کم کردن تخفیف اگر وجود داشت
    discount = session.get("discount", 0)


    if discount:

        total -= discount


        if total < 0:

            total = 0



    order = Order(

        customer_name=session["user"],

        roblox_username=session["roblox_username"],

        phone=session["phone"],

        products=products,

        total_price=total

    )


    db.session.add(order)

    db.session.commit()



    # پاک کردن سبد و تخفیف بعد از ثبت سفارش

    session["cart"] = []

    session.pop("discount", None)

    session.pop("discount_message", None)


    session.modified = True



    return redirect("/order")







# ثبت نام
@app.route("/register", methods=["GET","POST"])
def register():

    error = None



    if request.method == "POST":


        name = request.form["name"]

        email = request.form["email"]

        roblox_username = request.form["roblox_username"]

        phone = request.form["phone"]

        password = request.form["password"]



        old_user = User.query.filter_by(email=email).first()



        if old_user:

            error = "این ایمیل قبلاً ثبت شده است ❌"



        else:


            user = User(

                name=name,

                email=email,

                roblox_username=roblox_username,

                phone=phone,

                password=password

            )


            db.session.add(user)

            db.session.commit()



            session["user"] = user.name

            session["roblox_username"] = user.roblox_username

            session["phone"] = user.phone



            return redirect("/order")




    return render_template(

        "register.html",

        error=error

    )









# ورود
@app.route("/login", methods=["GET","POST"])
def login():

    error = None



    if request.method == "POST":


        email = request.form["email"]

        password = request.form["password"]



        user = User.query.filter_by(

            email=email,

            password=password

        ).first()




        if user:


            session["user"] = user.name

            session["roblox_username"] = user.roblox_username

            session["phone"] = user.phone



            return redirect("/")



        else:

            error = "ایمیل یا رمز عبور اشتباه است ❌"




    return render_template(

        "login.html",

        error=error

    )








# صفحه سفارش
@app.route("/order")
def order():

    if "user" not in session:

        return redirect("/login")


    return render_template("order.html")


@app.route("/delete_code/<int:id>")
def delete_code(id):

    code = RedeemCode.query.get(id)


    if code:

        db.session.delete(code)

        db.session.commit()


    return redirect("/admin")


@app.route("/add_code", methods=["POST"])
def add_code():

    code = request.form["code"]

    reward = request.form["reward"]


    old_code = RedeemCode.query.filter_by(
        code=code
    ).first()


    if old_code:

        return redirect("/admin")


    new_code = RedeemCode(

        code=code,

        reward=reward

    )


    db.session.add(new_code)

    db.session.commit()


    return redirect("/admin")

@app.route("/admin")
def admin():

    orders = Order.query.order_by(
        Order.id.desc()
    ).all()


    codes = RedeemCode.query.order_by(
        RedeemCode.id.desc()
    ).all()


    claims = RedeemClaim.query.order_by(
        RedeemClaim.id.desc()
    ).all()


    spin_claims = SpinClaim.query.order_by(
        SpinClaim.id.desc()
    ).all()


    spin_rewards = SpinReward.query.order_by(
        SpinReward.id.desc()
    ).all()


    discounts = DiscountCode.query.order_by(
        DiscountCode.id.desc()
    ).all()


    items = Item.query.order_by(
        Item.id.desc()
    ).all()


    return render_template(
        "admin.html",

        orders=orders,

        codes=codes,

        claims=claims,

        spin_claims=spin_claims,

        spin_rewards=spin_rewards,

        discounts=discounts,

        items=items
    
    )



@app.route("/spin")
def spin():

    if "user" not in session:
        return redirect("/login")

    user_spin = UserSpin.query.filter_by(
        roblox_username=session["roblox_username"]
    ).first()

    spins = 0

    if user_spin:
        spins = user_spin.spins

    spin_message = session.pop("spin_message", None)

    return render_template(
        "spin.html",
        spin=spins,
        spin_message=spin_message
    )



@app.route("/redeem", methods=["GET","POST"])
def redeem():

    message = None


    if "user" not in session:
        return redirect("/login")


    if request.method == "POST":

        code_text = request.form["code"].strip()


        code = RedeemCode.query.filter_by(
            code=code_text
        ).first()



        if not code:

            message = "❌ همچین کدی وجود ندارد"



        else:

            used = code.used_users.split(",")


            if session["user"] in used:

                message = "❌ شما قبلاً از این کد استفاده کرده‌اید"



            else:

                used.append(session["user"])


                code.used_users = ",".join(used)



                claim = RedeemClaim(

                    username=session["user"],

                    roblox_username=session["roblox_username"],

                    phone=session["phone"],

                    code=code.code,

                    reward=code.reward

                )


                db.session.add(claim)

                db.session.commit()



                message = f"🎉 تبریک! شما برنده شدید: {code.reward}"



    return render_template(
        "redeem.html",
        message=message
    )








with app.app_context():
    db.create_all()


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



@app.route("/delete_order/<int:id>")
def delete_order(id):

    order = Order.query.get(id)

    if order:
        db.session.delete(order)
        db.session.commit()

    return redirect("/admin")


@app.route("/delete_redeem/<int:id>")
def delete_redeem(id):

    claim = RedeemClaim.query.get(id)

    if claim:
        db.session.delete(claim)
        db.session.commit()

    return redirect("/admin")



@app.route("/add_discount", methods=["POST"])
def add_discount():

    code = request.form["code"]
    amount = request.form["amount"]

    discount = DiscountCode(
        code=code,
        amount=int(amount)
    )

    db.session.add(discount)
    db.session.commit()

    return redirect("/admin")



@app.route("/delete_item/<int:id>")
def delete_item(id):

    item = Item.query.get_or_404(id)

    db.session.delete(item)

    db.session.commit()

    return redirect("/admin")


@app.route("/apply_discount", methods=["POST"])
def apply_discount():

    discount_code = request.form["discount_code"].strip()


    discount = DiscountCode.query.filter_by(
        code=discount_code
    ).first()


    if discount:

        username = session.get("user")


        used_users = discount.used_users.split(",")


        if username in used_users:

            session["discount_message"] = "❌ شما قبلاً از این کد استفاده کرده‌اید"

            session["discount"] = 0


        else:

            session["discount"] = discount.amount

            session["discount_message"] = f"✅ {discount.amount} تومان تخفیف اعمال شد"


            used_users.append(username)

            discount.used_users = ",".join(used_users)

            db.session.commit()



    else:

        session["discount"] = 0

        session["discount_message"] = "❌ کد تخفیف اشتباه است"



    return redirect("/cart")


def get_user_spin():

    roblox_username = session.get("roblox_username")

    if not roblox_username:
        return None


    user_spin = UserSpin.query.filter_by(
        roblox_username=roblox_username
    ).first()


    if not user_spin:

        user_spin = UserSpin(

            username=session.get("user"),

            roblox_username=roblox_username,

            phone=session.get("phone"),

            spins=0

        )

        db.session.add(user_spin)

        db.session.commit()


    return user_spin


def check_daily_spin():

    user_spin = get_user_spin()

    if not user_spin:
        return


    now = datetime.now()


    if user_spin.last_daily_spin is None:

        user_spin.spins += 1

        user_spin.last_daily_spin = now


    else:

        next_spin_time = user_spin.last_daily_spin + timedelta(hours=24)


        if now >= next_spin_time:

            user_spin.spins += 1

            user_spin.last_daily_spin = now


    db.session.commit()


if __name__ == "__main__":
 app.run(host="0.0.0.0", port=5000, debug=False)

