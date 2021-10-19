from itertools import product
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask.helpers import make_response
from flaskext.mysql import MySQL
from flask_wtf import FlaskForm
from wtforms import SelectField
import pdfkit

app = Flask(__name__)
#MySQL connection
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'flaskbill'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql=MySQL(app)

#Session
app.secret_key = 'mysecretkey'

@app.route('/')
def index():
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    lendata = len(data)
    cur.execute('SELECT * FROM ticket')
    dataticket = cur.fetchall()
    lenticket= len(dataticket)
    products = []
    for i in range(0,lendata):
        if data[i][3] == 0:
            pass
        else:
            products.append(data[i][1])
    productos=[]
    descuento=[]
    for i in range(0,lenticket):
        valueitem = dataticket[i][3]
        if valueitem == 0:
            descuento.append(dataticket[i])
        else:
            productos.append(dataticket[i])

    lenprod = len(productos)
    listfinprod=[]
    for i in range(0,lenprod):
        listfinprod.append(productos[i][1]) 
    productfinal = list(set(products) - set(listfinprod))    
    lendesc= len(descuento)
    if lendesc == 0:
        if lenprod == 0:
            total=0
        elif lenprod == 1:
            total=productos[0][4]
        else:
            total = 0
            for i in range(0,lenprod):
                subtotalitem = productos[i][4]
                total += subtotalitem 
    else:
        if lenprod == 0:
            total=0
        elif lenprod == 1:
            total=productos[0][4]
            total = total - descuento[0][4]
            if total < 0:
                total = 0
            else:
                total = total
        else:
            total = 0
            for i in range(0,lenprod):
                subtotalitem = productos[i][4]
                total += subtotalitem
            total = total - descuento[0][4]

    return render_template('index.html', products=productfinal,ticket=productos,lenticket=lenprod, total=total, descuento=descuento, lendesc=lendesc)

@app.route('/price/<product>')
def bill(product):
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM productos WHERE product = %s',(product))
    data = cur.fetchall()
    price = data[0][2]
    priceok = str(price)
    return priceok

@app.route('/subt/<cant>/<price>')
def subt(cant=None,price=None):
    cant=int(cant)
    price=int(price)
    subtotal = cant*price
    subtotalok = str(subtotal)
    return subtotalok

@app.route('/cant/<product>')
def cant(product):
    print('oli')
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM productos WHERE product = %s',(product))
    data = cur.fetchall()
    cant = int(data[0][3])
    cants = str(cant)
    return cants

@app.route('/promo', methods=['POST'])
def promo():
    if request.method == 'POST':
        codigo = request.form['codigo'] 
        conn = mysql.connect()
        cur= conn.cursor()
        cur.execute('SELECT * FROM codigos WHERE codigo = %s',(codigo))
        data = cur.fetchall()
        cur.execute('SELECT * FROM ticket WHERE price = 0')
        datanumcod = cur.fetchall()
        numcod = len(datanumcod)
        if len(data) == 0:
            flash('El código que ingresaste no es valido')
        else:
            if numcod == 0:
                descuento = data[0][2]
                conn = mysql.connect()
                cur= conn.cursor()
                cur.execute("INSERT INTO ticket(product, cant, price, subtotal) VALUES (%s, %s, %s, %s)", (codigo, 0, 0, descuento))
                conn.commit()               
            else:
                id= datanumcod[0][0]
                descuento = data[0][2]
                cur.execute("""
                    UPDATE ticket 
                    SET product = %s, 
                    cant = %s, 
                    price= %s,
                    subtotal= %s
                    WHERE id= %s
                    """,
                    (codigo, 0, 0, descuento, id))
                conn.commit()

        return redirect(url_for('index')) 


@app.route('/add_ticket', methods=['POST'])
def add_ticket():
    if request.method == 'POST':
        product = request.form['product']
        price = request.form['price']
        cant = request.form['cant']
        subtotal = request.form['subtotal']
        conn = mysql.connect()
        cur= conn.cursor()
        cur.execute("INSERT INTO ticket(product, cant, price, subtotal) VALUES (%s, %s, %s, %s)", (product, cant, price, subtotal))
        conn.commit()
        return redirect(url_for('index'))    

        
@app.route('/sumar/<id>')
def sumar(id):
    conn=mysql.connect()
    cur=conn.cursor()
    cur.execute('SELECT * FROM ticket WHERE id = %s',(id))
    data = cur.fetchall()
    cant=data[0][2]
    producto = data[0][1]
    precio = data[0][3]
    cur.execute('SELECT * FROM productos WHERE product = %s',(producto))
    prodstockdata=cur.fetchall()
    prodstock=prodstockdata[0][3]
    if cant < prodstock:
        cant += 1
        subtotal = cant*precio
        cur.execute("""
            UPDATE ticket 
            SET product = %s, 
            cant = %s, 
            price= %s,
            subtotal= %s
            WHERE id= %s
            """,
            (producto, cant, precio, subtotal, id))
        conn.commit()

    elif cant == prodstock:
        flash("Solo hay " + str(prodstock) + " unidades de " + producto + " en stock") 
    return producto
    
@app.route('/restar/<id>')
def restar(id):
    conn=mysql.connect()
    cur=conn.cursor()
    cur.execute('SELECT * FROM ticket WHERE id = %s',(id))
    data = cur.fetchall()
    cant=data[0][2]
    producto = data[0][1]
    precio = data[0][3]
    if cant > 1:
        cant -= 1
        subtotal = cant*precio
        cur.execute("""
            UPDATE ticket 
            SET product = %s, 
            cant = %s, 
            price= %s,
            subtotal= %s
            WHERE id= %s
            """,
            (producto, cant, precio, subtotal, id))
        conn.commit()

    elif cant == 1:
        cur.execute('DELETE FROM ticket WHERE id = {0}'.format(id))
        conn.commit()
    return producto    

@app.route('/delete/<id>')
def delete_item(id):
    conn=mysql.connect()
    cur=conn.cursor()
    cur.execute('DELETE FROM ticket WHERE id = {0}'.format(id))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/invoice')
def invoice():
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    cur.execute('SELECT * FROM ticket')
    dataticket = cur.fetchall()
    lenticket= len(dataticket)
    productos=[]
    descuento=[]
    for i in range(0,lenticket):
        valueitem = dataticket[i][3]
        if valueitem == 0:
            descuento.append(dataticket[i])
        else:
            productos.append(dataticket[i])

    lenprod = len(productos)
    lendesc= len(descuento)
    if lendesc == 0:
        if lenprod == 0:
            total=0
        elif lenprod == 1:
            total=productos[0][4]
        else:
            total = 0
            for i in range(0,lenprod):
                subtotalitem = productos[i][4]
                total += subtotalitem 
    else:
        if lenprod == 0:
            total=0
        elif lenprod == 1:
            total=productos[0][4]
            total = total - descuento[0][4]
            if total < 0:
                total = 0
            else:
                total = total
        else:
            total = 0
            for i in range(0,lenprod):
                subtotalitem = productos[i][4]
                total += subtotalitem
            total = total - descuento[0][4]

    return render_template('invoice.html', products=data,ticket=productos,lenticket=lenprod, total=total, descuento=descuento, lendesc=lendesc)

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    if request.method == 'POST':
        conn = mysql.connect()
        cur= conn.cursor()
        cur.execute('SELECT * FROM productos')
        data = cur.fetchall()
        cur.execute('SELECT * FROM ticket')
        dataticket = cur.fetchall()
        lenticket= len(dataticket)
        productos=[]
        descuento=[]
        for i in range(0,lenticket):
            valueitem = dataticket[i][3]
            if valueitem == 0:
                descuento.append(dataticket[i])
            else:
                productos.append(dataticket[i])

        lenprod = len(productos)
        lendesc= len(descuento)
        if lendesc == 0:
            if lenprod == 0:
                total=0
            elif lenprod == 1:
                total=productos[0][4]
            else:
                total = 0
                for i in range(0,lenprod):
                    subtotalitem = productos[i][4]
                    total += subtotalitem 
        else:
            if lenprod == 0:
                total=0
            elif lenprod == 1:
                total=productos[0][4]
                total = total - descuento[0][4]
                if total < 0:
                    total = 0
                else:
                    total = total
            else:
                total = 0
                for i in range(0,lenprod):
                    subtotalitem = productos[i][4]
                    total += subtotalitem
                total = total - descuento[0][4]

        rendered = render_template('pdf.html', products=data,ticket=productos,lenticket=lenprod, total=total, descuento=descuento, lendesc=lendesc)
        options = {
                "enable-local-file-access": None
                    }
        pdf = pdfkit.from_string(rendered,False,options=options,)
        response = make_response(pdf)
        response.headers['content-Type'] = 'aplication/pdf'
        response.headers['content-Disposition'] = 'inline; filename=invoice.pdf'
        return response
    
@app.route('/terminar')
def terminar():
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM ticket')
    ticketdata=cur.fetchall()
    lenticket=len(ticketdata)
    for i in range(0,lenticket):
        producto=ticketdata[i][1]
        cant=ticketdata[i][2]
        precio=ticketdata[i][3]
        cur.execute('SELECT * FROM productos WHERE product = %s',(producto))
        prodinfo = cur.fetchall()
        stock=prodinfo[0][3]
        stockfinal = stock - cant
        cur.execute("""
            UPDATE productos 
            SET product = %s, 
            price = %s, 
            stock= %s
            WHERE product= %s
            """,
            (producto, precio, stockfinal, producto))
        conn.commit()

    cur.execute('DELETE FROM ticket;')
    conn.commit()
    return redirect(url_for('index'))
    


@app.route('/inventory')
def inventory():
    conn = mysql.connect()
    cur= conn.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    return render_template('inventory.html', products=data)
    

@app.route('/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        product = request.form['product']
        price = request.form['price']
        stock = request.form['stock']
        conn = mysql.connect()
        cur= conn.cursor()
        cur.execute("INSERT INTO productos(product, price, stock) VALUES (%s, %s, %s)", (product, price, stock))
        conn.commit()
        flash('Producto agregado')
        return redirect(url_for('inventory'))    

@app.route('/edit_product/<id>')
def get_product(id):
    conn=mysql.connect()
    cur=conn.cursor()
    cur.execute('SELECT * FROM productos WHERE id = %s',(id))
    data = cur.fetchall()
    cur.execute('SELECT * FROM productos')
    dataprod = cur.fetchall()
    return render_template('edit-product.html', product = data[0],products=dataprod)

@app.route('/update_product/<id>', methods=['POST'])
def update_product(id):
    if request.method == 'POST':
        product = request.form['product']
        price = request.form['price']
        stock = request.form['stock']
        conn = mysql.connect()
        cur= conn.cursor()
        cur.execute("""
            UPDATE productos 
            SET product = %s, 
            price = %s, 
            stock= %s
            WHERE id = %s
            """,
            (product, price, stock, id))
        conn.commit()
        flash('Producto actualizado')
        return redirect(url_for('inventory'))

@app.route('/delete_product/<string:id>')
def delete_product(id):
    conn=mysql.connect()
    cur=conn.cursor()
    cur.execute('DELETE FROM productos WHERE id = {0}'.format(id))
    conn.commit()
    flash('Producto removido')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(port = 3000, debug = True)
    
