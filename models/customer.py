from extensions import db

class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), default='Umum')
    no_hp = db.Column(db.String(20))
    tipe = db.Column(db.String(20), default='dine_in')  # dine_in, take_away, delivery
    penjualan = db.relationship('Penjualan', back_populates='customer', lazy=True)
    

    def __repr__(self):
        return f'<Customer {self.nama}>'
